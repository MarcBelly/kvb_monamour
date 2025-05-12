from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import mysql.connector
from database.db_connection import get_all_users


auth = Blueprint("auth", __name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Inesbelly",
        database="kvb_monamour"
    )

@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        Pseudo = request.form["Pseudo"]
        Nom = request.form["Nom"]
        Email = request.form["Email"]
        password = request.form["password"]
        image = request.files.get("image")
        image_path = None

        if image and image.filename:
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            image.save(image_path)
            image_path = f"uploads/{filename}"

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE Pseudo = %s", (Pseudo,))
        if cursor.fetchone():
            return "Ce pseudo existe déjà"

        hashed_pw = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (Pseudo, Nom, Email, password_hash, image_path, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (Pseudo, Nom, Email, hashed_pw, image_path, 0))
        db.commit()
        cursor.close()
        db.close()

# Connecter l'utilisateur directement après l'inscription
        session["user_id"] = cursor.lastrowid  # Utilise user_id dans la session
        session["pseudo"] = Pseudo
        session["email"] = Email
        session["is_admin"] = 0  # L'utilisateur n'est pas admin par défaut

        return redirect(url_for("auth.login"))

    return render_template("signup.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pseudo = request.form["Pseudo"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE Pseudo = %s", (pseudo,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["pseudo"] = user["Pseudo"]
            session["is_admin"] = user["is_admin"]

            return redirect(url_for("auth.admin")) if user["is_admin"] else redirect(url_for("auth.profil"))
        else:
            return render_template("login.html", error="Identifiants incorrects.")

    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
    
    users = get_all_users()
    return render_template("admin.html", users=users)

@auth.route('/profil')
def profil():
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
    return render_template("profil.html")

