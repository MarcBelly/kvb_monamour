import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from kvb_calcul import calculer_kvb_ma100, calculer_kvb_me100, calculer_kvb_me120
from auth.routes import auth, calculer_rang_et_progression
from database.db_connection import mydb_connection, get_or_create_table, delete_user_by_id
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.register_blueprint(auth, url_prefix='/auth')

db = mydb_connection()
get_or_create_table(db)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    warning = None
    type_train = None
    masse_totale = None
    masse_freinee = None

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    db_cursor = db.cursor(dictionary=True)
    db_cursor.execute(
        "SELECT pseudo, image_path FROM users WHERE id = %s",
        (session["user_id"],)
    )

    user = db_cursor.fetchone()
    db_cursor.close()

    result = warning = type_train = masse_totale = masse_freinee = None


    if request.method == "POST":
        type_train = request.form.get("type_train")
        masse_totale = request.form.get("masse_totale")
        masse_freinee = request.form.get("masse_freinee")

        try:
            masse_totale = int(float(masse_totale))
            masse_freinee = int(float(masse_freinee))

            db_cursor = db.cursor()

            if type_train == "MA100":
                result = calculer_kvb_ma100(masse_totale, masse_freinee, type_train)
                db_cursor.execute("UPDATE users SET count_ma100 = count_ma100 + 1 WHERE id = %s", (session["user_id"],))
            elif type_train == "ME100":
                result = calculer_kvb_me100(masse_totale, masse_freinee, type_train)
                db_cursor.execute("UPDATE users SET count_me100 = count_me100 + 1 WHERE id = %s", (session["user_id"],))
            elif type_train == "ME120":
                result = calculer_kvb_me120(masse_totale, masse_freinee, type_train)
                db_cursor.execute("UPDATE users SET count_me120 = count_me120 + 1 WHERE id = %s", (session["user_id"],))
            
            db.commit()
            db_cursor.close()

        except ValueError:
            warning = "Veuillez entrer des valeurs numériques valides."

    return render_template("home.html", user=user, result=result, warning=warning,
                           type_train=type_train, masse_totale=masse_totale,
                           masse_freinee=masse_freinee)

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return "Accès interdit", 403

    from database.db_connection import get_all_users
    users_raw = get_all_users()

    users = []
        # définis d’abord tes seuils/noms (ou importe-les d’ailleurs)
    seuils_ma100 = [100, 200, 300]
    noms_ma100   = ["Apprenti du MA100", "Fonctionnaire du MA100", "Administrateur du MA100", "Expert du MA100"]
    seuils_me100 = [100, 200, 300]
    noms_me100   = ["Apprenti du ME100", "Grand bourgeois du ME100", "Patron du ME100", "Baron du ME100"]
    seuils_me120 = [100, 200, 300]
    noms_me120   = ["Hostile du ME120", "Mécanicien du ME120", "Conducteur du ME120", "Chef de meute ME120"]

    for user in users_raw:
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
            # Tu peux exposer le nom du rang et/ou le pourcentage
            "rang_ma100": prog_ma100["nom"],
            "pct_ma100": int((c_ma100 / prog_ma100["next"]) * 100),
            "rang_me100": prog_me100["nom"],
            "pct_me100": int((c_me100 / prog_me100["next"]) * 100),
            "rang_me120": prog_me120["nom"],
            "pct_me120": int((c_me120 / prog_me120["next"]) * 100),
        })

    return render_template("admin.html", users=users, progress_ma100=prog_ma100, progress_me100=prog_me100, progress_me120=prog_me120)

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    # 1) Vérification admin
    if not session.get("is_admin"):
        return "Accès interdit", 403

    # 2) Empêcher l’admin de se supprimer lui-même (optionnel mais recommandé)
    if user_id == session.get("user_id"):
        flash("Vous ne pouvez pas vous supprimer vous-même.", "warning")
        return redirect(url_for("admin"))

    # 3) Appel à la fonction de suppression en base
    success = delete_user_by_id(user_id)
    if success:
        flash("Utilisateur supprimé avec succès.", "success")
    else:
        flash("Erreur lors de la suppression.", "danger")

    # 4) Retour à la liste
    return redirect(url_for("admin"))

@app.route('/info')
def info():
    return render_template('info.html')


if __name__ == "__main__":
    app.run(debug=True)
