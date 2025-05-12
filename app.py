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

            if type_train == "MA100":
                result = calculer_kvb_ma100(masse_totale, masse_freinee, type_train)
            elif type_train == "ME100":
                result = calculer_kvb_me100(masse_totale, masse_freinee, type_train)
            elif type_train == "ME120":
                result = calculer_kvb_me120(masse_totale, masse_freinee, type_train)
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
    users = get_all_users()
    return render_template("admin.html", users=users)

if __name__ == "__main__":
    app.run(debug=True)
