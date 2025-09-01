from database.db_connection import mydb_connection
from werkzeug.security import generate_password_hash
import os

def create_admin():
    Pseudo = os.getenv("ADMIN_USERNAME", "admin")
    Nom = os.getenv("ADMIN_NAME", "Admin")
    Email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "adminpass")
    password_hash = generate_password_hash(password)
    image_path = ""
    is_admin = True

    db = mydb_connection()
    cur = db.cursor()

    # pas de USE: la base est déjà sélectionnée par la connexion
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    try:
        cur.execute("""
            INSERT INTO users (Pseudo, Nom, Email, password_hash, image_path, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              Nom = VALUES(Nom),
              password_hash = VALUES(password_hash),
              image_path = VALUES(image_path),
              is_admin = VALUES(is_admin)
        """, (Pseudo, Nom, Email, password_hash, image_path, is_admin))
        db.commit()
        print(f"✅ Compte admin '{Pseudo}' créé/mis à jour.")
    except Exception as e:
        db.rollback()
        print("❌ Erreur :", e)
    finally:
        cur.close()
        db.close()

if __name__ == "__main__":
    create_admin()
