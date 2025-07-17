from flask import Flask, render_template, request, session
from kvb_calcul import calculer_kvb_ma100, calculer_kvb_me100, calculer_kvb_me120
import os

app = Flask(__name__)
app.secret_key = "ma_clé_secrète"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    warning = None
    type_train = None
    masse_totale = None
    masse_freinee = None

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

    return render_template("home.html", result=result, warning=warning,
                           type_train=type_train, masse_totale=masse_totale,
                           masse_freinee=masse_freinee)

if __name__ == "__main__":
    app.run(debug=True)
