import mysql.connector
import os

def mydb_connection():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Inesbelly",
        database=""
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

#def add_new_user(db, curseur, text_prenom, text_nom, text_sexe, text_pseudo):

    #insert_query = "INSERT INTO users (Pseudo, Nom, Email, Pseudo) VALUES (%s, %s, %s, %s)"
        #values = (text_prenom, text_nom, text_sexe, text_pseudo)
        #curseur.execute(insert_query, values)
        #db.commit()
        #curseur.close()
        #db.close()
        #return True
    
   #except mysql.Error:
        #db.rollback()
        #curseur.close()
        #db.close()
        #return False