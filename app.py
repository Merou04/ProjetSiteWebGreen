from flask import (Flask, render_template, request,
                   redirect, url_for, abort, session, g)
import sqlite3, os
from database import init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

DB = 'greenspot.db'

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

# ── Accueil ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    db    = get_db()
    spots = db.execute(
        'SELECT s.id, s.titre, s.type_terrain, s.ensoleillement, '
        '       s.date_creation, u.nom '
        'FROM spots s JOIN users u ON s.auteur_id = u.id '
        'ORDER BY s.date_creation DESC LIMIT 3'
    ).fetchall()
    return render_template('index.html', spots=spots, images=IMAGES_SPOTS)

# ── Les routes vers les pages ───────────────────────────────────────────────────────
@app.route('/index')
def accueil():
    return redirect(url_for('index'))

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

@app.route('/page_spots')
def page_spots():
    return render_template('spots.html')


# ── Liste spots ───────────────────────────────────────────────────────
@app.route('/spots')
def spots():
    db       = get_db()
    page     = request.args.get('page', 1, type=int)
    per_page = 20
    offset   = (page - 1) * per_page
    spots = db.execute(
        'SELECT s.id, s.titre, s.type_terrain, s.ensoleillement, '
        '       s.date_creation, u.nom '
        'FROM spots s JOIN users u ON s.auteur_id = u.id '
        'ORDER BY s.date_creation DESC LIMIT ? OFFSET ?',
        [per_page, offset]
    ).fetchall()
    total       = db.execute('SELECT COUNT(*) FROM spots').fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template('spots.html', spots=spots, page=page,
                           total_pages=total_pages, images=IMAGES_SPOTS)

# ── Détail spot ───────────────────────────────────────────────────────
@app.route('/spots/<int:id>')
def spot_detail(id):
    db   = get_db()
    spot = db.execute(
        'SELECT s.*, u.nom AS auteur_nom '
        'FROM spots s JOIN users u ON s.auteur_id = u.id '
        'WHERE s.id = ?', [id]
    ).fetchone()
    if spot is None:
        abort(404)
    return render_template('spot_detail.html', spot=spot, images=IMAGES_SPOTS)

# ── Créer spot ────────────────────────────────────────────────────────
@app.route('/spots/new', methods=['GET', 'POST'])
def spot_new():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    errors    = {}
    form_data = {}

    if request.method == 'POST':
        titre          = request.form.get('titre',          '').strip()
        description    = request.form.get('description',    '').strip()
        latitude       = request.form.get('latitude',       '').strip()
        longitude      = request.form.get('longitude',      '').strip()
        type_terrain   = request.form.get('type_terrain',   '').strip()
        ensoleillement = request.form.get('ensoleillement', '').strip()

        form_data = request.form

        if not titre or len(titre) < 3:
            errors['titre'] = 'Le titre doit faire au moins 3 caractères.'
        if len(titre) > 100:
            errors['titre'] = 'Le titre ne doit pas dépasser 100 caractères.'
        if not description or len(description) < 10:
            errors['description'] = 'La description doit faire au moins 10 caractères.'
        try:
            lat = float(latitude)
            if not (-90 <= lat <= 90):
                errors['latitude'] = 'Latitude invalide (entre -90 et 90).'
        except ValueError:
            errors['latitude'] = 'Latitude invalide.'
        try:
            lng = float(longitude)
            if not (-180 <= lng <= 180):
                errors['longitude'] = 'Longitude invalide (entre -180 et 180).'
        except ValueError:
            errors['longitude'] = 'Longitude invalide.'
        if type_terrain not in TYPES_TERRAIN:
            errors['type_terrain'] = 'Choisir un type de terrain.'
        if ensoleillement not in ENSOLEILLEMENTS:
            errors['ensoleillement'] = 'Choisir un ensoleillement.'

        if not errors:
            db = get_db()
            db.execute(
                'INSERT INTO spots '
                '(titre, description, latitude, longitude, '
                ' type_terrain, ensoleillement, auteur_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                [titre, description, float(latitude), float(longitude),
                 type_terrain, ensoleillement, session['user_id']]
            )
            db.commit()
            return redirect(url_for('spots'))

    return render_template('spot_new.html',
                           errors=errors,
                           form_data=form_data,
                           types_terrain=TYPES_TERRAIN,
                           ensoleillements=ENSOLEILLEMENTS)

# ── Modifier spot ─────────────────────────────────────────────────────
@app.route('/spots/<int:id>/edit', methods=['GET', 'POST'])
def spot_edit(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db   = get_db()
    spot = db.execute('SELECT * FROM spots WHERE id = ?', [id]).fetchone()
    if spot is None:
        abort(404)
    if spot['auteur_id'] != session['user_id'] and session.get('role') != 'admin':
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
            return redirect(url_for('spot_detail', id=id))

    return render_template('spot_edit.html', spot=spot, errors=errors,
                           form_data=form_data,
                           types_terrain=TYPES_TERRAIN,
                           ensoleillements=ENSOLEILLEMENTS)

# ── Supprimer spot ────────────────────────────────────────────────────
@app.route('/spots/<int:id>/delete', methods=['POST'])
def spot_delete(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db   = get_db()
    spot = db.execute('SELECT * FROM spots WHERE id = ?', [id]).fetchone()
    if spot is None:
        abort(404)
    if spot['auteur_id'] != session['user_id'] and session.get('role') != 'admin':
        abort(403)
    db.execute('DELETE FROM spots WHERE id = ?', [id])
    db.commit()
    return redirect(url_for('spots'))

# ── Auth (stubs — à compléter) ────────────────────────────────────────
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── Init BDD au démarrage si absente ─────────────────────────────────
import os as _os
if not _os.path.exists(DB):
    init_db()

if __name__ == '__main__':
    app.run(debug=True)