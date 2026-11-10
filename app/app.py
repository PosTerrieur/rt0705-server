"""Point d'entrée du tiers présentation : site web de la vidéothèque (Flask + Jinja)"""
import os

from flask import Flask, flash, redirect, render_template, request, url_for

import auth
import routes
from affichage import FILTRES
from api_client import ErreurApi

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cle-de-developpement-a-changer")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,    # cookie inaccessible au JavaScript
    SESSION_COOKIE_SAMESITE="Lax",   # pas envoyé lors d'un POST venant d'un autre site
)

for blueprint in routes.BLUEPRINTS:
    app.register_blueprint(blueprint)

app.jinja_env.filters.update(FILTRES)


@app.context_processor
def variables_communes():
    """Variables disponibles dans tous les templates"""
    return {"utilisateur": auth.utilisateur_courant(), "est_admin": auth.est_admin()}


@app.template_global()
def url_page(page):
    """URL de la page courante avec un autre numéro de page (pagination)"""
    arguments = request.args.to_dict()
    arguments["page"] = page
    return url_for(request.endpoint, **request.view_args, **arguments)


# --- Réponses de l'API non traitées par les routes ---------------------------------

@app.errorhandler(ErreurApi)
def erreur_api(erreur):
    if erreur.statut == 401:
        # Jeton expiré ou révoqué (compte désactivé, déconnexion)
        auth.fermer_session()
        flash("Votre session a expiré : reconnectez-vous", "warning")
        return redirect(url_for("compte.connexion", suivant=auth.page_courante()))
    statut = erreur.statut if erreur.statut in (400, 403, 404, 409) else 503
    return render_template("erreur.html", statut=statut, message=erreur.message), statut


@app.errorhandler(404)
def page_inconnue(_erreur):
    return render_template("erreur.html", statut=404, message="Cette page n'existe pas"), 404
