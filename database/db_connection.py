import os
import mysql.connector
from urllib.parse import urlparse

def mydb_connection():
    scalingo_url = os.getenv("SCALINGO_MYSQL_URL")
    if scalingo_url:
        url = urlparse(scalingo_url)
        return mysql.connector.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path.lstrip('/'),
            port=url.port
        )
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "kvb_user"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "kvb_monamour")
    )

    return db

def get_or_create_table(db):
    curseur = db.cursor()
    curseur.execute(f"CREATE DATABASE IF NOT EXISTS kvb_monamour ")
    curseur.execute(f"USE kvb_monamour")
    curseur.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, Pseudo VARCHAR(150) UNIQUE NOT NULL, Nom VARCHAR(150), Email VARCHAR(255) UNIQUE, password_hash VARCHAR(255) NOT NULL, image_path VARCHAR(255), is_admin BOOLEAN DEFAULT FALSE, count_ma100 INT DEFAULT 0, count_me100 INT DEFAULT 0, count_me120 INT DEFAULT 0);")

    return curseur
    
def get_all_users(database='kvb_monamour', table='users'):
    db = mydb_connection()
    curseur = db.cursor()

    try: 
        curseur.execute(f"USE kvb_monamour")
        curseur.execute(f"SELECT * FROM {table}")
        liste_users = curseur.fetchall()
        curseur.close()
        db.close()
        return liste_users
    
    except mysql.Error:
        db.rollback()
        curseur.close()
        db.close()
        return None

def delete_user_by_id(user_id: int, table='users', database='kvb_monamour') -> bool:
    """
    Supprime l'utilisateur d'id `user_id` dans la base et la table spécifiées.
    Retourne True si un enregistrement a été supprimé, False sinon.
    """
    db = mydb_connection()
    curseur = db.cursor()
    try:
        curseur.execute(f"USE {database}")
        curseur.execute(f"DELETE FROM {table} WHERE id = %s", (user_id,))
        db.commit()
        return curseur.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Erreur lors de la suppression de l'utilisateur {user_id}: {e}")
        db.rollback()
        return False
    finally:
        curseur.close()
        db.close()
