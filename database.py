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
            titre          TEXT    NOT NULL,
            description    TEXT    NOT NULL,
            latitude       REAL    NOT NULL,
            longitude      REAL    NOT NULL,
            type_terrain   TEXT    NOT NULL,
            ensoleillement TEXT    NOT NULL,
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

if __name__ == '__main__':
    init_db()