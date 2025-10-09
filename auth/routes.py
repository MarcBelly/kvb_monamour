import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, current_app, g, send_file
)
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database.db_connection import mydb_connection

# Blueprint d'authentification
auth = Blueprint("auth", __name__)

# ---------------------
# Connexion DB par requête
# ---------------------
def get_db():
    """Retourne la connexion DB pour la requête courante"""
    if "db" not in g:
        g.db = mydb_connection()
    return g.db

@auth.teardown_request
def _teardown_db(exception=None):
    """Ferme proprement la DB après chaque requête"""
    db = g.pop("db", None)
    if db is not None:
        db.close()

# ---------------------
# Gestion des rangs utilisateurs
# ---------------------
def calculer_rang_et_progression(count, seuils, noms):
    """Retourne le rang et le prochain seuil à atteindre."""
    rang_idx = sum(count >= s for s in seuils)
    nom = noms[rang_idx]
    seuil_suivant = seuils[rang_idx] if rang_idx < len(seuils) else seuils[-1]
    return {"idx": rang_idx, "nom": nom, "count": count, "next": seuil_suivant}

# ---------------------
# Inscription
# ---------------------
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        Pseudo = request.form["Pseudo"].strip()
        Nom = request.form["Nom"].strip()
        Email = request.form["Email"].strip()
        password = request.form["password"]
        image = request.files.get("image")
        image_path = None

        # Gestion de l'image uploadée -> stockée en DB (BLOB)
        avatar_blob = None
        avatar_mime = None
        image_path = None  # on n'utilise plus le disque pour les avatars

        image = request.files.get("image")
        if image and image.filename:
            avatar_blob = image.read()
            avatar_mime = image.mimetype or "image/jpeg"


        db = get_db()
        cursor = db.cursor()

        # Vérifier si le pseudo existe déjà
        cursor.execute("SELECT id FROM users WHERE Pseudo = %s", (Pseudo,))
        if cursor.fetchone():
            cursor.close()
            return render_template("signup.html", error="Ce pseudo existe déjà.")

        hashed_pw = generate_password_hash(password)
        cursor.execute(
            """
            INSERT INTO users (Pseudo, Nom, Email, password_hash, image_path, is_admin, avatar_blob, avatar_mime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (Pseudo, Nom, Email, hashed_pw, image_path, 0, avatar_blob, avatar_mime),
        )
        db.commit()
        user_id = cursor.lastrowid
        cursor.close()

        # Connexion automatique après inscription
        session["user_id"] = user_id
        session["pseudo"] = Pseudo
        session["email"] = Email
        session["is_admin"] = 0

        return redirect(url_for("auth.profil"))

    return render_template("signup.html")

# ---------------------
# Connexion
# ---------------------
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pseudo = (request.form.get("Pseudo") or "").strip()
        password = request.form.get("password") or ""

        print("[LOGIN] reçu:", {"Pseudo": pseudo, "has_password": bool(password)})

        if not pseudo or not password:
            return render_template("login.html", error="Veuillez remplir les deux champs.")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        # insensible à la casse + trim
        cursor.execute("SELECT * FROM users WHERE LOWER(Pseudo) = LOWER(%s)", (pseudo,))
        user = cursor.fetchone()
        cursor.close()

        print("[LOGIN] user trouvé ?", bool(user))
        if user:
            ok = check_password_hash(user["password_hash"], password)
            print("[LOGIN] check_password_hash:", ok, "is_admin:", user["is_admin"])
            if ok:
                session["user_id"] = user["id"]
                session["pseudo"]  = user["Pseudo"]
                session["is_admin"] = bool(user["is_admin"])
                return redirect(url_for("admin") if session["is_admin"] else url_for("auth.profil"))

        return render_template("login.html", error="Identifiants incorrects.")

    return render_template("login.html")


# ---------------------
# Déconnexion
# ---------------------
@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

# ---------------------
# Avatar binaire depuis la base (add le 09/10)
# ---------------------
@auth.route("/avatar/<int:user_id>")
def avatar(user_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT avatar_blob, avatar_mime FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()

    if row and row.get("avatar_blob"):
        return send_file(BytesIO(row["avatar_blob"]),
                         mimetype=row.get("avatar_mime") or "image/jpeg",
                         as_attachment=False,
                         download_name=f"avatar_{user_id}.jpg")

    # Fallback: image par défaut versionnée (persistante)
    return redirect(url_for('static', filename='uploads/pic-no-pic.png'))


# ---------------------
# Profil utilisateur
# ---------------------
@auth.route("/profil", methods=["GET", "POST"])
def profil():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT image_path, count_ma100, count_me100, count_me120
        FROM users WHERE id = %s
        """,
        (session["user_id"],),
    )
    user = cur.fetchone()
    cur.close()

    if not user:
        return "Utilisateur non trouvé", 404

    # Compteurs utilisateurs
    c_ma100 = user.get("count_ma100") or 0
    c_me100 = user.get("count_me100") or 0
    c_me120 = user.get("count_me120") or 0

    # Seuils et noms de rangs
    seuils_ma100 = [100, 200, 300]
    noms_ma100 = ["Apprenti du MA100", "Fonctionnaire du MA100", "Administrateur du MA100", "Expert du MA100"]
    seuils_me100 = [100, 200, 300]
    noms_me100 = ["Apprenti du ME100", "Grand bourgeois du ME100", "Patron du ME100", "Baron du ME100"]
    seuils_me120 = [100, 200, 300]
    noms_me120 = ["Hostile du ME120", "Mécanicien du ME120", "Conducteur du ME120", "Chef de meute ME120"]

    prog_ma100 = calculer_rang_et_progression(c_ma100, seuils_ma100, noms_ma100)
    prog_me100 = calculer_rang_et_progression(c_me100, seuils_me100, noms_me100)
    prog_me120 = calculer_rang_et_progression(c_me120, seuils_me120, noms_me120)

    return render_template(
        "profil.html",
        user=user,
        progress_ma100=prog_ma100,
        progress_me100=prog_me100,
        progress_me120=prog_me120,
        image_path=user.get("image_path"),
    )

# ---------------------
# Upload image profil
# ---------------------
@auth.route("/upload_profile_picture", methods=["POST"])
def upload_profile_picture():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    image = request.files.get("image")
    if image and image.filename:
        avatar_blob = image.read()
        avatar_mime = image.mimetype or "image/jpeg"

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET avatar_blob = %s, avatar_mime = %s, image_path = NULL WHERE id = %s",
            (avatar_blob, avatar_mime, session["user_id"])
        )
        db.commit()
        cursor.close()

    return redirect(url_for("auth.profil"))

