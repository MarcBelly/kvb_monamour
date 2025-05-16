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

            return redirect(url_for("admin")) if user["is_admin"] else redirect(url_for("auth.profil"))
        else:
            return render_template("login.html", error="Identifiants incorrects.")

    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth.route('/profil', methods=["GET", "POST"])
def profil():
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT image_path, count_ma100, count_me100, count_me120 FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if not user:
        return "Utilisateur non trouvé", 404

    count_ma100 = user["count_ma100"] or 0
    count_me100 = user["count_me100"] or 0
    count_me120 = user["count_me120"] or 0
    total = count_ma100 + count_me100 + count_me120

    def calculer_rang(total):
        if total >= 100:
            return "Expert ferroviaire comme Alex Leduc"
        elif total >= 50:
            return "Déjà un ancien du rail"
        elif total >= 20:
            return "CDR confirmé"
        else:
            return "Apprenti conducteur comme le Dam's"

    rang = calculer_rang(total)
    image_path = user.get("image_path")

    return render_template("profil.html", user=user, count_ma100=count_ma100, count_me100=count_me100, count_me120=count_me120, total=total, rang=rang, image_path=image_path)

@auth.route("/upload_profile_picture", methods=["POST"])
def upload_profile_picture():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    image = request.files.get("image")
    if image and image.filename:
        filename = secure_filename(image.filename)
        image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        image.save(image_path)

        relative_path = f"uploads/{filename}"

        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET image_path = %s WHERE id = %s", (relative_path, session["user_id"]))
        db.commit()
        cursor.close()
        db.close()

        session["image_path"] = relative_path  # Pour stocker temporairement

    return redirect(url_for("auth.profil"))
