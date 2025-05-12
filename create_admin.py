from database.db_connection import mydb_connection
from werkzeug.security import generate_password_hash

def create_admin():
    db = mydb_connection()
    cursor = db.cursor()
    cursor.execute("USE kvb_monamour")

    Pseudo = "admin"
    Nom = "Admin"
    Email = "admin@example.com"
    password = "adminpass"
    password_hash = generate_password_hash(password)
    image_path = ""
    is_admin = True


    try:
        cursor.execute("""
            INSERT INTO users (Pseudo, Nom, Email, password_hash, image_path, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (Pseudo, Nom, Email, password_hash, image_path,  is_admin))
        db.commit()
        print("✅ Compte admin créé.")
    except Exception as e:
        print("❌ Erreur :", e)
        db.rollback()

    cursor.close()
    db.close()

create_admin()
