from flask import Flask, render_template, request
from kvb_calcul import calculer_kvb_ma100, calculer_kvb_me100, calculer_kvb_me120

app = Flask(__name__)

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

            if type_train == "MA100":
                result = calculer_kvb_ma100(masse_totale, masse_freinee, type_train)
            elif type_train == "ME100":
                result = calculer_kvb_me100(masse_totale, masse_freinee, type_train)
            elif type_train == "ME120":
                result = calculer_kvb_me120(masse_totale, masse_freinee, type_train)
            else:
                warning = "Invalide!"

        except ValueError:
            warning = "Veuillez entrer des valeurs numériques valides."

    return render_template("home.html", result=result, warning=warning,
                           type_train=type_train, masse_totale=masse_totale,
                           masse_freinee=masse_freinee)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
