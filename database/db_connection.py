# database/db_connection.py
import os
import mysql.connector
from urllib.parse import urlparse, parse_qs, unquote

def _from_dsn(dsn: str) -> dict:
    """
    Parse une URL de type mysql://user:pass@host:port/db?params
    Retourne un dict d'arguments pour mysql.connector.connect(...)
    """
    u = urlparse(dsn)
    params = parse_qs(u.query or "")
    # Décodage user/pass + nom de base
    user = unquote(u.username) if u.username else None
    pwd  = unquote(u.password) if u.password else None
    db   = u.path.lstrip("/") if u.path else None

    # TLS: Scalingo peut fournir ?useSSL=true&verifyServerCertificate=false
    # mysql-connector active TLS automatiquement si le serveur l'impose.
    # On n'essaie PAS de forcer des options non supportées.
    conn_kwargs = dict(
        host=u.hostname,
        port=u.port or 3306,
        user=user,
        password=pwd,
        database=db,
        autocommit=True,
        charset="utf8mb4",
    )
    return conn_kwargs

def mydb_connection():
    """
    PROD: lit SCALINGO_MYSQL_URL (ou DATABASE_URL).
    DEV:  lit DB_HOST/DB_USER/DB_PASSWORD/DB_NAME depuis .env.
    """
    dsn = os.getenv("SCALINGO_MYSQL_URL") or os.getenv("DATABASE_URL")
    if dsn:
        conn = mysql.connector.connect(**_from_dsn(dsn))
        # Sécurise contre les connexions inactives : ping si nécessaire
        try:
            conn.ping(reconnect=True, attempts=1, delay=0)
        except Exception:
            # En cas d'échec, on ré-ouvre
            conn.close()
            conn = mysql.connector.connect(**_from_dsn(dsn))
        return conn

    # --- Fallback DEV local ---
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "kvb_user"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "kvb_monamour"),
        autocommit=True,
        charset="utf8mb4",
    )
    try:
        conn.ping(reconnect=True, attempts=1, delay=0)
    except Exception:
        conn.close()
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "kvb_user"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "kvb_monamour"),
            autocommit=True,
            charset="utf8mb4",
        )
    return conn


def get_or_create_table(db):
    """
    En prod, la base existe déjà (sélectionnée via l'URL).
    On crée juste la table si besoin.
    """
    cur = db.cursor()
    cur.execute("""
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.close()


def get_all_users(table: str = "users"):
    db = mydb_connection()
    cur = db.cursor()
    try:
        cur.execute(f"SELECT * FROM {table}")
        return cur.fetchall()
    except mysql.connector.Error as e:
        print("get_all_users error:", e)
        return []
    finally:
        cur.close()
        db.close()


def delete_user_by_id(user_id: int, table: str = "users") -> bool:
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
