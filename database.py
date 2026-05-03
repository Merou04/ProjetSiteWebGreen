import sqlite3

DB = 'greenspot.db'

def init_db():
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
            image          TEXT,
            acces          TEXT,
            tags           TEXT,
            map_url        TEXT,
            date_creation  DATETIME DEFAULT CURRENT_TIMESTAMP,
            auteur_id      INTEGER NOT NULL,
            FOREIGN KEY (auteur_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_spots_date
            ON spots(date_creation);
        CREATE INDEX IF NOT EXISTS idx_spots_auteur
            ON spots(auteur_id);
    ''')
    conn.commit()
    conn.close()
    print('✅ Base de données initialisée.')

    """Insère les spots initiaux si la table est vide."""
    conn = sqlite3.connect(DB)
    count = conn.execute('SELECT COUNT(*) FROM spots').fetchone()[0]
    if count > 0:
        conn.close()
        return

    spots = [
        ('Jardin des Plantes',    'Plantes médicinales et tropicales au cœur de Paris. Sol riche, idéal pour observer la biodiversité végétale.',      48.844360,  2.360430, 'cour',       'mi_ombre',    1),
        ('Serres d\'Auteuil',     'Immenses serres abritant des plantes tropicales et exotiques. Ambiance unique, humidité élevée.',                     48.847900,  2.254300, 'cour',       'plein_soleil', 1),
        ('Jardin du Luxembourg',  'Verger historique et roseraie au centre de Paris. Nombreuses espèces florales bien entretenues.',                     48.846200,  2.337200, 'cour',       'plein_soleil', 1),
        ('Buttes-Chaumont',       'Parc sauvage avec forte biodiversité urbaine. Falaises, prairies, zones ombragées variées.',                          48.879500,  2.382900, 'cour',       'mi_ombre',    1),
        ('Parc de Belleville',    'Massifs fleuris en terrasses avec vue sur Paris. Exposition plein sud, très ensoleillé.',                             48.870700,  2.381600, 'jardiniere', 'plein_soleil', 1),
        ('Jardin Albert-Kahn',    'Jardins du monde recréés sur 4 hectares à Boulogne. Diversité exceptionnelle de végétaux.',                           48.841700,  2.231500, 'cour',       'mi_ombre',    1),
    ]

    conn.executemany(
    'INSERT INTO spots (titre, description, image, acces, tags, map_url, auteur_id) VALUES (?,?,?,?,?,?,?)',
    spots
    )
    conn.commit()
    conn.close()
    print('✅ Spots initiaux insérés.')

def seed_spots():
    """Insère les spots initiaux correspondant aux cartes HTML."""
    conn = sqlite3.connect(DB)
    # On vérifie si la table est déjà remplie
    count = conn.execute('SELECT COUNT(*) FROM spots').fetchone()[0]
    if count > 0:
        conn.close()
        return

    # Structure : (titre, description, image, acces, tags, map_url, auteur_id)
    spots = [
        (
            'Jardin des Plantes', 
            'Plantes médicinales & tropicales', 
            'jardin-plantes.webp', 
            'Métro Jussieu / vélo', 
            'Botanique,Gratuit', 
            'https://maps.google.com/?q=57+Rue+Cuvier+Paris', 
            1
        ),
        (
            'Serres d’Auteuil', 
            'Plantes tropicales', 
            'serres-auteuil.webp', 
            'Métro Porte d’Auteuil', 
            'Exotique', 
            "https://maps.google.com/?q=Serres+d'Auteuil", 
            1
        ),
        (
            'Jardin du Luxembourg', 
            'Verger & roseraie', 
            'luxembourg.webp', 
            'RER Luxembourg', 
            'Historique,Romantique', 
            'https://maps.google.com/?q=Jardin+du+Luxembourg', 
            1
        ),
        (
            'Buttes-Chaumont', 
            'Biodiversité urbaine', 
            'buttes-chaumont.webp', 
            'Métro 7bis', 
            'Nature', 
            'https://maps.google.com/?q=Buttes+Chaumont', 
            1
        ),
        (
            'Parc de Belleville', 
            'Massifs fleuris', 
            'belleville.webp', 
            'Métro Belleville', 
            'Vue', 
            'https://maps.google.com/?q=Parc+de+Belleville', 
            1
        ),
        (
            'Jardin Albert-Kahn', 
            'Jardins du monde', 
            'albert-kahn.webp', 
            'Métro Boulogne', 
            'Voyage', 
            'https://maps.google.com/?q=Jardin+Albert+Kahn', 
            1
        )
    ]

    conn.executemany(
        'INSERT INTO spots (titre, description, image, acces, tags, map_url, auteur_id) VALUES (?,?,?,?,?,?,?)',
        spots
    )
    conn.commit()
    conn.close()
    print('✅ Spots initiaux insérés.')

if __name__ == '__main__':
    init_db()
    seed_spots()