import os
from flask import Flask, render_template, request, session, redirect, url_for, flash, g, current_app
from kvb_calcul import calculer_kvb_ma100, calculer_kvb_me100, calculer_kvb_me120
from auth.routes import auth, calculer_rang_et_progression
from database.db_connection import mydb_connection, get_or_create_table, delete_user_by_id
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")

# Uploads (attention: le FS de Scalingo est éphémère)
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Enregistrer le blueprint d'auth
app.register_blueprint(auth, url_prefix="/auth")

# ---- Connexion DB par requête + teardown ----
def get_db():
    if "db" not in g:
        g.db = mydb_connection()
    return g.db

@app.teardown_request
def _teardown_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# ---- Init schéma minimal au boot (safe) ----
try:
    _db = mydb_connection()
    get_or_create_table(_db)
    _db.close()
except Exception as e:
    print("Init DB warning:", e)

# -------------------- ROUTES --------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Récupérer l'utilisateur courant
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT Pseudo AS pseudo, image_path FROM users WHERE id = %s",
        (session["user_id"],)
    )
    user = cur.fetchone()
    cur.close()

    result = None
    warning = None
    type_train = None
    masse_totale = None
    masse_freinee = None
    is_text = False

    if request.method == "POST":
        type_train = request.form.get("type_train")
        masse_totale = request.form.get("masse_totale")
        masse_freinee = request.form.get("masse_freinee")
        try:
            masse_totale = int(float(masse_totale))
            masse_freinee = int(float(masse_freinee))

            cur = db.cursor()
            if type_train == "MA100":
                result = calculer_kvb_ma100(masse_totale, masse_freinee, type_train)
                cur.execute("UPDATE users SET count_ma100 = count_ma100 + 1 WHERE id = %s", (session["user_id"],))
            elif type_train == "ME100":
                result = calculer_kvb_me100(masse_totale, masse_freinee, type_train)
                cur.execute("UPDATE users SET count_me100 = count_me100 + 1 WHERE id = %s", (session["user_id"],))
            elif type_train == "ME120":
                result = calculer_kvb_me120(masse_totale, masse_freinee, type_train)
                cur.execute("UPDATE users SET count_me120 = count_me120 + 1 WHERE id = %s", (session["user_id"],))
            db.commit()
            cur.close()

            try:
                float(result)  # si convertible en float -> nombre
                is_text = False
            except (ValueError, TypeError):
                is_text = True  # sinon -> texte

        except ValueError:
            warning = "Veuillez entrer des valeurs numériques valides."
            is_text = True
            result = warning

    return render_template(
        "home.html",
        user=user,
        result=result,
        is_text=is_text,
        warning=warning,
        type_train=type_train,
        masse_totale=masse_totale,
        masse_freinee=masse_freinee,
    )

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return "Accès interdit", 403

    users_raw = (delete_user_by_id and None)  # juste pour éviter les linters
    from database.db_connection import get_all_users
    users_raw = get_all_users() or []

    users = []

    # Seuils / noms (peuvent être déplacés dans un module dédié)
    seuils_ma100 = [100, 200, 300]
    noms_ma100   = ["Apprenti du MA100", "Fonctionnaire du MA100", "Administrateur du MA100", "Expert du MA100"]
    seuils_me100 = [100, 200, 300]
    noms_me100   = ["Apprenti du ME100", "Grand bourgeois du ME100", "Patron du ME100", "Baron du ME100"]
    seuils_me120 = [100, 200, 300]
    noms_me120   = ["Hostile du ME120", "Mécanicien du ME120", "Conducteur du ME120", "Chef de meute ME120"]

    for user in users_raw:
        # user = (id, Pseudo, Nom, Email, password_hash, image_path, is_admin, count_ma100, count_me100, count_me120)
        c_ma100 = user[7] or 0
        c_me100 = user[8] or 0
        c_me120 = user[9] or 0

        prog_ma100 = calculer_rang_et_progression(c_ma100, seuils_ma100, noms_ma100)
        prog_me100 = calculer_rang_et_progression(c_me100, seuils_me100, noms_me100)
        prog_me120 = calculer_rang_et_progression(c_me120, seuils_me120, noms_me120)

        users.append({
            "id": user[0],
            "pseudo": user[1],
            "email": user[3],
            "is_admin": user[6],
            "count_ma100": c_ma100,
            "count_me100": c_me100,
            "count_me120": c_me120,
            "image_path": user[5],
            "rang_ma100": prog_ma100["nom"],
            "pct_ma100": int((c_ma100 / prog_ma100["next"]) * 100) if prog_ma100["next"] else 0,
            "rang_me100": prog_me100["nom"],
            "pct_me100": int((c_me100 / prog_me100["next"]) * 100) if prog_me100["next"] else 0,
            "rang_me120": prog_me120["nom"],
            "pct_me120": int((c_me120 / prog_me120["next"]) * 100) if prog_me120["next"] else 0,
        })

    return render_template("admin.html", users=users)

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    # 1) Vérification admin
    if not session.get("is_admin"):
        return "Accès interdit", 403

    # 2) Empêcher l’admin de se supprimer lui-même
    if user_id == session.get("user_id"):
        flash("Vous ne pouvez pas vous supprimer vous-même.", "warning")
        return redirect(url_for("admin"))

    # 3) Suppression
    success = delete_user_by_id(user_id)
    flash("Utilisateur supprimé avec succès." if success else "Erreur lors de la suppression.", "success" if success else "danger")
    return redirect(url_for("admin"))

@app.route("/info")
def info():
    return render_template("info.html")

if __name__ == "__main__":
    app.run(debug=True)
