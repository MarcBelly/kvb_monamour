from flask import Blueprint

auth = Blueprint(
    'auth',
    __name__,
    static_folder='static',  #  C'est ce qu'il te manque !
    template_folder='templates'  # si tu as des templates dans auth/templates
)
