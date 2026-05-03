GREENSPOT - readme -


database.py: fonctions créant les schémas des tables et commandes sql
app.py: backend en flask --> ecrit en python
greenspot.db : la bdd
templates: contient les pages html
static: dossier pososedant les styles des pages, img

----------------- COMMENT CODER DES FONCTIONNALITÉS SUR LE PROJET ?---------------------------------

Pour ajouter une fonctionnalité côté backend sur GREENSPOT, il faut intervenir principalement dans trois fichiers :

database.py
app.py
le fichier HTML correspondant dans templates/
1. Ajouter / modifier la base de données (database.py)

C’est ici que tu définis la structure des données.

Ajouter une table :
def create_table_example(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS example (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            value TEXT
        )
    """)
Ajouter une requête SQL (insert, select, etc.) :
def insert_example(conn, name, value):
    conn.execute("INSERT INTO example (name, value) VALUES (?, ?)", (name, value))
    conn.commit()

👉 Toujours passer par ce fichier pour interagir avec la base (greenspot.db).

2. Créer la logique backend (app.py)

Ici tu relies tes routes Flask avec la base de données.

Exemple de route :
@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name")
    value = request.form.get("value")

    conn = get_db_connection()
    insert_example(conn, name, value)

    return redirect("/")

👉 C’est ici que tu :

récupères les données des formulaires
appelles les fonctions de database.py
renvoies une page ou rediriges
3. Modifier / créer la page (templates/*.html)

Créer une interface utilisateur.

Exemple de formulaire :
<form action="/add" method="post">
    <input type="text" name="name" placeholder="Nom">
    <input type="text" name="value" placeholder="Valeur">
    <button type="submit">Ajouter</button>
</form>

👉 Le action doit correspondre à une route dans app.py.

4. Ajouter du style ou des assets (static/)
CSS → static/style.css
Images → static/img/

Dans le HTML :

<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">



------- LES FONCTIONNALITES DEVELOPPEES :-------------------------------------
 - via la page des spots on peut AJOUTER un spot
