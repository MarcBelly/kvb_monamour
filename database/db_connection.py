import os
import mysql.connector
from urllib.parse import urlparse, unquote

def mydb_connection():
    """
    En prod (Scalingo), on lit SCALINGO_MYSQL_URL.
    En local, on lit les variables .env.
    """
    scalingo_url = os.getenv("SCALINGO_MYSQL_URL")
    if scalingo_url:
        url = urlparse(scalingo_url)
        user = unquote(url.username) if url.username else None
        pwd  = unquote(url.password) if url.password else None
        db   = url.path.lstrip('/') if url.path else None
        return mysql.connector.connect(
            host=url.hostname,
            port=url.port or 3306,
            user=user,
            password=pwd,
            database=db,
            charset='utf8mb4',
            autocommit=True
        )

    # Fallback local (dev)
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "kvb_user"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "kvb_monamour"),
        charset='utf8mb4',
        autocommit=True
    )

def get_or_create_table(db):
    """
    En prod, la base existe déjà et on est déjà connecté dessus.
    On crée juste la table si besoin.
    """
    curseur = db.cursor()
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Pseudo VARCHAR(150) UNIQUE NOT NULL,
            Nom VARCHAR(150),
            Email VARCHAR(255) UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            image_path VARCHAR(255),
            is_admin BOOLEAN DEFAULT FALSE,
            count_ma100 INT DEFAULT 0,
            count_me100 INT DEFAULT 0,
            count_me120 INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    curseur.close()

def get_all_users(table='users'):
    db = mydb_connection()
    cur = db.cursor()
    try:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        db.close()

def delete_user_by_id(user_id: int, table='users') -> bool:
    db = mydb_connection()
    cur = db.cursor()
    try:
        cur.execute(f"DELETE FROM {table} WHERE id = %s", (user_id,))
        db.commit()
        return cur.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Erreur suppression utilisateur {user_id}: {e}")
        db.rollback()
        return False
    finally:
        cur.close()
        db.close()

