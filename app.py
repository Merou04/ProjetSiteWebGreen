from flask import (Flask, render_template, request,
                   redirect, url_for, abort, session, g, flash)
import sqlite3, os, re
from database import init_db, hash_password, verify_password
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

DB = 'greenspot.db'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

IMAGES_SPOTS = {
    'balcon':     'balcon.webp',
    'pied_arbre': 'pied_arbre.webp',
    'jardiniere': 'jardiniere.webp',
    'cour':       'cour.webp',
}
TYPES_TERRAIN   = ['balcon', 'pied_arbre', 'jardiniere', 'cour']
ENSOLEILLEMENTS = ['plein_soleil', 'mi_ombre', 'ombre']

# ── BDD ───────────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

# ── AUTH MIDDLEWARE ET DÉCORATEURS ────────────────────────────────────

@app.before_request
def load_logged_in_user():
    """Middleware : charger utilisateur actuel dans g.user"""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

def require_login(f):
    """Décorateur pour protéger les routes et nécessiter une connexion."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash('Vous devez vous connecter d\'abord.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Décorateur pour les routes administrateur."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or g.user['role'] not in ('admin', 'moderator'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Vérifier si l'extension du fichier est autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Route pour récupérer les images depuis la BDD ────────────────────
@app.route('/image/<int:spot_id>')
def get_image(spot_id):
    """Servir l'image d'un spot depuis la base de données."""
    db = get_db()
    spot = db.execute('SELECT image FROM spots WHERE id = ?', (spot_id,)).fetchone()
    
    if not spot or not spot['image']:
        abort(404)
    
    return app.response_class(
        response=spot['image'],
        mimetype='image/webp'
    )

def convert_to_webp(file):
    """Convertir une image en WebP et retourner les données binaires."""
    try:
        from io import BytesIO
        
        # Ouvrir l'image avec Pillow
        img = Image.open(file)
        
        # Convertir en RGB si PNG avec transparence
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Convertir en WebP optimisé pour le web (green IT) et retourner les données binaires
        img_buffer = BytesIO()
        img.save(img_buffer, 'WEBP', quality=80, optimize=True)
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
    except Exception as e:
        return None

# ── Accueil ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')
    

# ── Les routes vers les pages ───────────────────────────────────────────────────────


@app.route('/conseils')
def conseils():
    return render_template('conseils.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/plants')
def plants():
    # Ici tu pourras plus tard passer une liste de plantes depuis la BDD
    return render_template('plants.html')

@app.route('/inscription')
def inscription():
    return render_template('register.html')

# ── Liste spots ───────────────────────────────────────────────────────
@app.route('/spots')
def spots():
    db       = get_db()
    page     = request.args.get('page', 1, type=int)
    per_page = 20
    offset   = (page - 1) * per_page
    query = request.args.get('q', '')

    spots = db.execute(
        'SELECT id, titre, description, image, acces, tags, map_url, auteur_id '
        'FROM spots '
        'ORDER BY date_creation DESC LIMIT ? OFFSET ?',
        [per_page, offset]
    ).fetchall()

    total       = db.execute('SELECT COUNT(*) FROM spots').fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)

    if query:
        # On cherche dans le titre, la description ou la ville
        # Le symbole % permet de chercher "n'importe où dans le texte"
        search_pattern = f"%{query}%"
        spots = db.execute("""
            SELECT * FROM spots 
            WHERE titre LIKE ? OR description LIKE ? OR ville LIKE ?
            ORDER BY date_creation DESC
        """, (search_pattern, search_pattern, search_pattern)).fetchall()
    else:
        spots = db.execute("SELECT * FROM spots ORDER BY date_creation DESC").fetchall()

    return render_template('spots.html', spots=spots,
                           page=page, total_pages=total_pages, last_query=query)


# ── Détail spot ───────────────────────────────────────────────────────
@app.route('/spot/<int:spot_id>', methods=['GET', 'POST'])
def spot_detail(spot_id):
    limit = request.args.get('limit', 5, type=int)
    db = get_db()

    total_reviews = db.execute(
        "SELECT COUNT(*) FROM reviews WHERE spot_id = ?", (spot_id,)
    ).fetchone()[0]
    
    # Si l'utilisateur poste un commentaire
    if request.method == 'POST':
        if not g.user:
            flash('Vous devez être connecté pour laisser un commentaire.', 'warning')
            return redirect(url_for('login'))
            
        note = request.form.get('note')
        comm = request.form.get('commentaire')
        
        # Validation
        try:
            note = int(note)
            if not (1 <= note <= 5):
                raise ValueError
        except (ValueError, TypeError):
            flash('Note invalide (doit être entre 1 et 5).', 'danger')
            return redirect(url_for('spot_detail', spot_id=spot_id))
        
        if not comm or len(comm.strip()) < 5:
            flash('Le commentaire doit faire au moins 5 caractères.', 'warning')
            return redirect(url_for('spot_detail', spot_id=spot_id))
        
        # Insérer avec requête paramétrée
        db.execute(
            "INSERT INTO reviews (spot_id, user_id, note, commentaire) VALUES (?, ?, ?, ?)",
            (spot_id, g.user['id'], note, comm.strip())
        )
        db.commit()
        flash('Votre commentaire a été ajouté !', 'success')

        return redirect(url_for('spot_detail', spot_id=spot_id))

    # Récupérer les infos du spot
    spot = db.execute("SELECT * FROM spots WHERE id = ?", (spot_id,)).fetchone()
    
    if not spot:
        abort(404)
    
    # Récupérer les commentaires avec le nom de l'utilisateur
    reviews = db.execute("""
        SELECT r.*, u.prenom, u.nom 
        FROM reviews r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.spot_id = ? 
        ORDER BY r.date_publication DESC
        LIMIT ?
    """, (spot_id,limit)).fetchall()

    return render_template('spot_detail.html', spot=spot, reviews=reviews,total_reviews=total_reviews,current_limit=limit)

# ── Créer spot ────────────────────────────────────────────────────────
@app.route('/spots/new', methods=['GET', 'POST'])
@require_login
def spot_new():
    if not g.user:
        return redirect(url_for('login'))

    errors    = {}
    form_data = {}

    if request.method == 'POST':
        titre       = request.form.get('titre',       '').strip()
        description = request.form.get('description', '').strip()
        acces       = request.form.get('acces',       '').strip()
        tags        = request.form.get('tags',        '').strip()
        map_url     = request.form.get('map_url',     '').strip()
        image_file  = request.files.get('image')

        form_data = request.form

        # Validation
        if not titre or len(titre) < 3:
            errors['titre'] = 'Le titre doit faire au moins 3 caractères.'
        if len(titre) > 100:
            errors['titre'] = 'Le titre ne doit pas dépasser 100 caractères.'
        if not description or len(description) < 10:
            errors['description'] = 'La description doit faire au moins 10 caractères.'
        if not image_file:
            errors['image'] = 'Veuillez choisir une image.'
        elif not allowed_file(image_file.filename):
            errors['image'] = 'Format non supporté. Utilisez JPG, PNG ou WebP.'
        elif image_file.content_length > MAX_FILE_SIZE:
            errors['image'] = 'L\'image dépasse 5 MB.'
        
        if not acces:
            errors['acces'] = "L'accès est requis."
        if not tags:
            errors['tags'] = 'Au moins un tag requis.'

        valid_domains = ["google.com/maps", "goo.gl", "maps.app.goo.gl"]

        if not map_url or not any(domain in map_url for domain in valid_domains):
            errors['map_url'] = 'Le lien doit être un lien Google Maps valide.'

        if not errors:
            # Convertir l'image en WebP et récupérer les données binaires
            image_data = convert_to_webp(image_file)
            if not image_data:
                errors['image'] = 'Erreur lors de la conversion de l\'image.'
            else:
                db = get_db()
                db.execute(
                    'INSERT INTO spots (titre, description, image, acces, tags, map_url, auteur_id) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    [titre, description, image_data, acces, tags, map_url, g.user['id']]
                )
                db.commit()
                flash('Spot créé avec succès ! 🌱', 'success')
                return redirect(url_for('spots'))

    return render_template('spot_new.html',
                           errors=errors,
                           form_data=form_data)
          

# ── Modifier spot ─────────────────────────────────────────────────────
@app.route('/spots/<int:id>/edit', methods=['GET', 'POST'])
@require_login
def spot_edit(id):
    db   = get_db()
    spot = db.execute('SELECT * FROM spots WHERE id = ?', [id]).fetchone()
    if spot is None:
        abort(404)
    # Vérification des droits : propriétaire ou admin
    if spot['auteur_id'] != g.user['id'] and g.user['role'] not in ('admin', 'moderator'):
        abort(403)

    errors    = {}
    form_data = spot

    if request.method == 'POST':
        titre          = request.form.get('titre',          '').strip()
        description    = request.form.get('description',    '').strip()
        latitude       = request.form.get('latitude',       '').strip()
        longitude      = request.form.get('longitude',      '').strip()
        type_terrain   = request.form.get('type_terrain',   '').strip()
        ensoleillement = request.form.get('ensoleillement', '').strip()
        form_data      = request.form

        if not titre or len(titre) < 3:
            errors['titre'] = 'Le titre doit faire au moins 3 caractères.'
        if not description or len(description) < 10:
            errors['description'] = 'La description doit faire au moins 10 caractères.'
        try:
            lat = float(latitude)
            lng = float(longitude)
        except ValueError:
            errors['coords'] = 'Coordonnées invalides.'

        if not errors:
            db.execute(
                'UPDATE spots SET titre=?, description=?, latitude=?, longitude=?, '
                'type_terrain=?, ensoleillement=? WHERE id=?',
                [titre, description, float(latitude), float(longitude),
                 type_terrain, ensoleillement, id]
            )
            db.commit()
            flash('Spot modifié avec succès !', 'success')
            return redirect(url_for('spot_detail', spot_id=id))

    return render_template('spot_edit.html', spot=spot, errors=errors,
                           form_data=form_data,
                           types_terrain=TYPES_TERRAIN,
                           ensoleillements=ENSOLEILLEMENTS)

# ── Supprimer spot ────────────────────────────────────────────────────
@app.route('/spots/<int:id>/delete', methods=['POST'])
@require_login
def spot_delete(id):
    db   = get_db()
    spot = db.execute('SELECT * FROM spots WHERE id = ?', [id]).fetchone()
    if spot is None:
        abort(404)
    # Vérification des droits
    if spot['auteur_id'] != g.user['id'] and g.user['role'] not in ('admin', 'moderator'):
        abort(403)
    db.execute('DELETE FROM spots WHERE id = ?', [id])
    db.commit()
    flash('Spot supprimé avec succès.', 'info')
    return redirect(url_for('spots'))

# ── LOGIN ─────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        errors = {}

        # Validation basique
        if not email:
            errors['email'] = 'L\'email est requis.'
        if not password:
            errors['password'] = 'Le mot de passe est requis.'

        if not errors:
            db = get_db()
            # Requête paramétrée contre injection SQL
            user = db.execute(
                'SELECT * FROM users WHERE LOWER(email) = ?',
                (email.lower(),)
            ).fetchone()

            if user and verify_password(password, user['mot_de_passe']):
                # Authentification réussie
                session.clear()
                session['user_id'] = user['id']
                session['role'] = user['role']
                flash(f'Bienvenue {user["prenom"]} !', 'success')
                return redirect(url_for('spots'))
            else:
                errors['auth'] = 'Email ou mot de passe incorrect.'

        return render_template('login.html', errors=errors, form_data=request.form)

    return render_template('login.html', errors={}, form_data={})

# ── REGISTER ──────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        prenom = request.form.get('prenom', '').strip()
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        errors = {}

        # Validation
        if not prenom or len(prenom) < 2:
            errors['prenom'] = 'Le prénom doit faire au moins 2 caractères.'
        if not nom or len(nom) < 2:
            errors['nom'] = 'Le nom doit faire au moins 2 caractères.'
        
        if not email or '@' not in email:
            errors['email'] = 'Veuillez entrer un email valide.'
        
        if not password or len(password) < 8:
            errors['password'] = 'Le mot de passe doit faire au moins 8 caractères.'
        
        if password != password_confirm:
            errors['password_confirm'] = 'Les mots de passe ne correspondent pas.'

        # Vérifier que l'email n'existe pas déjà (requête paramétrée)
        if not errors.get('email'):
            db = get_db()
            existing = db.execute(
                'SELECT id FROM users WHERE LOWER(email) = ?',
                (email.lower(),)
            ).fetchone()
            if existing:
                errors['email'] = 'Cet email est déjà utilisé.'

        if not errors:
            db = get_db()
            hashed_pwd = hash_password(password)
            try:
                cursor = db.execute(
                    'INSERT INTO users (prenom, nom, email, mot_de_passe, role) VALUES (?, ?, ?, ?, ?)',
                    (prenom, nom, email, hashed_pwd, 'user')
                )
                db.commit()
                user_id = cursor.lastrowid
                
                # Connecter automatiquement l'utilisateur
                session.clear()
                session['user_id'] = user_id
                session['role'] = 'user'
                
                flash('Inscription réussie ! Bienvenue sur GreenSpot.', 'success')
                return redirect(url_for('spots'))
            except sqlite3.IntegrityError:
                errors['email'] = 'Cet email est déjà utilisé.'

        return render_template('register.html', errors=errors, form_data=request.form)

    return render_template('register.html', errors={}, form_data={})

# ── LOGOUT ────────────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('index'))

# ── Init BDD au démarrage si absente ─────────────────────────────────
import os as _os
if not _os.path.exists(DB):
    init_db()
    from database import seed_all_data
    seed_all_data()

if __name__ == '__main__':
    app.run(debug=True)