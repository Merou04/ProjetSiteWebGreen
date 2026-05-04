import sqlite3
import bcrypt

DB = 'greenspot.db'

# ── Fonctions de hashage des mots de passe ───────────────────────────
def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_db():
    """Initialise la base de données avec les tables."""
    conn = sqlite3.connect(DB)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nom              TEXT    NOT NULL,
            prenom           TEXT    NOT NULL,
            email            TEXT    NOT NULL UNIQUE,
            mot_de_passe     TEXT    NOT NULL,
            role             TEXT    NOT NULL DEFAULT 'user',
            date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS spots (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            titre          TEXT NOT NULL,
            description    TEXT NOT NULL,
            image          BLOB,
            acces          TEXT,
            tags           TEXT,
            map_url        TEXT,
            date_creation  DATETIME DEFAULT CURRENT_TIMESTAMP,
            auteur_id      INTEGER NOT NULL,
            FOREIGN KEY (auteur_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER,
            user_id INTEGER,
            note INTEGER CHECK(note BETWEEN 1 AND 5),
            commentaire TEXT,
            date_publication DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(spot_id) REFERENCES spots(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_spots_date
            ON spots(date_creation);
        CREATE INDEX IF NOT EXISTS idx_spots_auteur
            ON spots(auteur_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_spot
            ON reviews(spot_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_user
            ON reviews(user_id);
        CREATE INDEX IF NOT EXISTS idx_users_email
            ON users(email);
                       
    ''')
    conn.commit()
    conn.close()
    print('✅ Base de données initialisée.')

def seed_all_data():
    """Crée et remplit la base avec des utilisateurs, des spots et des commentaires."""
    conn = sqlite3.connect(DB)
    
    # Vérifier si des données existent déjà
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count > 0:
        conn.close()
        print('✅ Base déjà peuplée.')
        return
    
    # ── Créer des utilisateurs ────────────────────────────────────────
    users = [
        ('Admin', 'Green', 'admin@greenspot.com', 'admin123', 'admin'),
        ('Jean', 'Dubois', 'jean@example.com', 'password123', 'user'),
        ('Marie', 'Martin', 'marie@example.com', 'password123', 'user'),
        ('Pierre', 'Bernard', 'pierre@example.com', 'password123', 'user'),
        ('Sophie', 'Garcia', 'sophie@example.com', 'password123', 'user'),
        ('Luc', 'Moreau', 'luc@example.com', 'password123', 'moderator'),
    ]
    
    user_ids = {}
    for prenom, nom, email, password, role in users:
        hashed_pwd = hash_password(password)
        cursor = conn.execute(
            'INSERT INTO users (prenom, nom, email, mot_de_passe, role) VALUES (?, ?, ?, ?, ?)',
            (prenom, nom, email, hashed_pwd, role)
        )
        user_ids[email] = cursor.lastrowid
        print(f'✅ Utilisateur créé: {prenom} {nom} ({role})')
    
    conn.commit()
    
    # ── Créer des spots ──────────────────────────────────────────────
    spots_data = [
        ('Jardin des Plantes', 
         'Plantes médicinales et tropicales au cœur de Paris. Sol riche et humide, idéal pour observer la biodiversité végétale. Excellente exposition partielle.',
         'jardin-plantes.webp',
         'Métro Jussieu, Bus 24, 57',
         'Botanique,Gratuit,Nature',
         'https://maps.google.com/?q=57+Rue+Cuvier+Paris',
         user_ids['admin@greenspot.com']),
        
        ('Serres d\'Auteuil',
         'Immenses serres abritant des plantes tropicales et exotiques. Ambiance chaude et humide, très bien entretenues. Parfait pour les plantes qui aiment la chaleur.',
         'serres-auteuil.webp',
         'Métro Porte d\'Auteuil, Bus 42',
         'Exotique,Chaleur,Humidité',
         'https://maps.google.com/?q=Serres+d\'Auteuil+Paris',
         user_ids['admin@greenspot.com']),
        
        ('Jardin du Luxembourg',
         'Verger historique et roseraie au centre de Paris. Nombreuses espèces florales bien entretenues, très ensoleillé. Atmosphère romantique et calme.',
         'luxembourg.webp',
         'RER Luxembourg, Bus 38, 82',
         'Historique,Romantique,Fleurs',
         'https://maps.google.com/?q=Jardin+du+Luxembourg+Paris',
         user_ids['jean@example.com']),
        
        ('Buttes-Chaumont',
         'Parc sauvage avec forte biodiversité urbaine. Falaises, prairies, zones ombragées variées. Idéal pour découvrir la flore sauvage parisienne.',
         'buttes-chaumont.webp',
         'Métro Buttes-Chaumont, Bus 60',
         'Nature,Biodiversité,Sauvage',
         'https://maps.google.com/?q=Buttes+Chaumont+Paris',
         user_ids['marie@example.com']),
        
        ('Parc de Belleville',
         'Massifs fleuris en terrasses avec vue panoramique sur Paris. Exposition plein sud, très ensoleillé. Parfait pour les plantes qui aiment le soleil.',
         'belleville.webp',
         'Métro Belleville, Bus 11, 60',
         'Vue,Ensoleillé,Terrasse',
         'https://maps.google.com/?q=Parc+de+Belleville+Paris',
         user_ids['pierre@example.com']),
        
        ('Jardin Albert-Kahn',
         'Jardins du monde recréés sur 4 hectares à Boulogne-Billancourt. Diversité exceptionnelle de végétaux : français, japonais, anglais, forêt.',
         'albert-kahn.webp',
         'Métro Boulogne, Bus 52',
         'Voyage,Diversité,4hectares',
         'https://maps.google.com/?q=Jardin+Albert+Kahn+Boulogne',
         user_ids['sophie@example.com']),
        
        ('Square des Peupliers',
         'Petit square urbain avec arbres matures et plantations basses. Ambiance paisible, beaucoup d\'ombre. Bon pour les plantes shade-tolerant.',
         'square-peupliers.webp',
         'Métro Alésia, Bus 38',
         'Urbain,Ombre,Calme',
         'https://maps.google.com/?q=Square+des+Peupliers+Paris',
         user_ids['luc@example.com']),
    ]
    
    spot_ids = []
    for titre, desc, image_filename, acces, tags, map_url, auteur_id in spots_data:
        # Charger l'image depuis le disque
        image_data = None
        image_path = f"static/img/spots/{image_filename}"
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
        except FileNotFoundError:
            print(f'⚠️  Image non trouvée: {image_path}')
        
        cursor = conn.execute(
            'INSERT INTO spots (titre, description, image, acces, tags, map_url, auteur_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (titre, desc, image_data, acces, tags, map_url, auteur_id)
        )
        spot_ids.append(cursor.lastrowid)
        print(f'✅ Spot créé: {titre}')
    
    conn.commit()
    
    # ── Créer des commentaires (reviews) ──────────────────────────────
    reviews_data = [
        (spot_ids[0], user_ids['jean@example.com'], 5, 'Magnifique ! Les plantes tropicales sont sublimes, bien entretenues. À voir absolument !'),
        (spot_ids[0], user_ids['marie@example.com'], 4, 'Très beau, mais un peu bondé les week-ends. Meilleur en semaine.'),
        (spot_ids[0], user_ids['pierre@example.com'], 5, 'Exceptionnel pour les botanistes. J\'ai trouvé plein d\'inspiration !'),
        
        (spot_ids[1], user_ids['sophie@example.com'], 5, 'Les serres sont incroyables ! Beaucoup d\'humidité, parfait pour mes plantes.'),
        (spot_ids[1], user_ids['jean@example.com'], 4, 'Bon mais très touristique. Préférer visite en fin d\'après-midi.'),
        (spot_ids[1], user_ids['luc@example.com'], 5, 'J\'y vais chaque mois, c\'est ma source d\'inspiration principale !'),
        
        (spot_ids[2], user_ids['pierre@example.com'], 5, 'Sublime roseraie ! Parfait pour les photos et se détendre.'),
        (spot_ids[2], user_ids['marie@example.com'], 4, 'Joli mais pas d\'ombre suffisante pour les plantes qui aiment l\'ombre.'),
        (spot_ids[2], user_ids['sophie@example.com'], 5, 'Un incontournable de Paris ! Toujours magnifique, quelle que soit la saison.'),
        
        (spot_ids[3], user_ids['luc@example.com'], 5, 'Biodiversité impressionnante ! J\'ai découvert plein de nouvelles plantes.'),
        (spot_ids[3], user_ids['jean@example.com'], 4, 'Accès un peu compliqué mais ça vaut le coup.'),
        
        (spot_ids[4], user_ids['sophie@example.com'], 5, 'Vue panoramique extraordinaire ! Les fleurs y poussent magnifiquement au soleil.'),
        (spot_ids[4], user_ids['marie@example.com'], 5, 'Mon endroit préféré à Paris. Ensoleillé, calme, idéal pour planter.'),
        
        (spot_ids[5], user_ids['jean@example.com'], 5, 'Un vrai voyage autour du monde ! Récréations de jardins très réalistes.'),
        (spot_ids[5], user_ids['pierre@example.com'], 4, 'Excellent pour apprendre les différents styles de jardinage.'),
        
        (spot_ids[6], user_ids['luc@example.com'], 4, 'Petit mais charmant. Bon pour les plantes d\'ombre. Calme et discret.'),
        (spot_ids[6], user_ids['marie@example.com'], 5, 'Parfait ! J\'ai trouvé l\'inspiration pour mon balcon ombragé.'),
    ]
    
    for spot_id, user_id, note, comment in reviews_data:
        conn.execute(
            'INSERT INTO reviews (spot_id, user_id, note, commentaire) VALUES (?, ?, ?, ?)',
            (spot_id, user_id, note, comment)
        )
        print(f'✅ Commentaire ajouté pour spot {spot_id}')
    
    conn.commit()
    conn.close()
    print('✅ Base de données complètement peuplée !')

if __name__ == '__main__':
    init_db()
    seed_all_data()
