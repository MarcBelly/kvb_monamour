from flask import Flask, render_template, request, session, redirect, url_for
from kvb_calcul import calculer_kvb_ma100, calculer_kvb_me100, calculer_kvb_me120
from auth.routes import auth
from database.db_connection import mydb_connection, get_or_create_table
import os

app = Flask(__name__)
app.secret_key = "ma_clé_secrète"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.register_blueprint(auth, url_prefix='/auth')

db = mydb_connection()
get_or_create_table(db)

def calculer_rang_app(total):
    if total >= 100:
        return "Expert ferroviaire comme Alex Leduc"
    elif total >= 50:
        return "Déjà un ancien du rail"
    elif total >= 20:
        return "CDR confirmé"
    else:
        return "Apprenti cdr comme le dam's"

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    warning = None
    type_train = None
    masse_totale = None
    masse_freinee = None

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    result = warning = type_train = masse_totale = masse_freinee = None


    if request.method == "POST":
        type_train = request.form.get("type_train")
        masse_totale = request.form.get("masse_totale")
        masse_freinee = request.form.get("masse_freinee")

        try:
            masse_totale = float(masse_totale)
            masse_freinee = float(masse_freinee)

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

    return render_template("home.html", result=result, warning=warning,
                           type_train=type_train, masse_totale=masse_totale,
                           masse_freinee=masse_freinee)

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return "Accès interdit", 403

    from database.db_connection import get_all_users
    users_raw = get_all_users()

    users = []
    for user in users_raw:
        # mapping: id, pseudo, nom, email, pw, img, is_admin, ma100, me100, me120
        total = (user[7] or 0) + (user[8] or 0) + (user[9] or 0)
        rang = calculer_rang_app(total)
        print(f"User {user[1]} total: {total}, rang: {rang}")
        users.append({
            "id": user[0],
            "pseudo": user[1],
            "email": user[3],
            "is_admin": user[6],
            "count_ma100": user[7] or 0,
            "count_me100": user[8] or 0,
            "count_me120": user[9] or 0,
            "image_path": user[5],
            "rang": rang
        })

    return render_template("admin.html", users=users)

if __name__ == "__main__":
    app.run(debug=True)
