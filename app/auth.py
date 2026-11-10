"""Session côté navigateur et contrôles de surface"""
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for


def ouvrir_session(reponse_connexion):
    """Enregistre en session ce que renvoie POST /api/sessions"""
    utilisateur = reponse_connexion["utilisateur"]
    session.clear()
    session["jeton"] = reponse_connexion["jeton"]
    session["utilisateur"] = {"id": utilisateur["id"], "login": utilisateur["login"],
                              "role": utilisateur["role"]}


def fermer_session():
    session.clear()


def utilisateur_courant():
    return session.get("utilisateur")


def est_admin():
    utilisateur = utilisateur_courant()
    return utilisateur is not None and utilisateur["role"] == "ADMIN"


def page_courante():
    """Chemin de la page demandée, pour y revenir après la connexion"""
    return request.full_path.rstrip("?")


def url_sure(suivant):
    """N'accepte que des chemins internes (évite les redirections vers un autre site)"""
    if suivant and suivant.startswith("/") and not suivant.startswith("//"):
        return suivant
    return url_for("catalogue.accueil")


def connexion_requise(vue):
    @wraps(vue)
    def vue_protegee(*args, **kwargs):
        if utilisateur_courant() is None:
            flash("Connectez-vous pour accéder à cette page", "warning")
            return redirect(url_for("compte.connexion", suivant=page_courante()))
        return vue(*args, **kwargs)
    return vue_protegee


def admin_requis(vue):
    @wraps(vue)
    def vue_protegee(*args, **kwargs):
        if utilisateur_courant() is None:
            flash("Connectez-vous pour accéder à cette page", "warning")
            return redirect(url_for("compte.connexion", suivant=page_courante()))
        if not est_admin():
            return render_template("erreur.html", statut=403,
                                   message="Cette page est réservée aux administrateurs"), 403
        return vue(*args, **kwargs)
    return vue_protegee
