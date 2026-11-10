"""Espace de l'utilisateur : connexion, profil, emprunts, retours, suivi (F01, F02, F10 à F12, F14)"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

import api_client as api
import auth
import formulaires
from affichage import date_fr
from api_client import ErreurApi

bp = Blueprint("compte", __name__)

PRETS_PAR_PAGE = 10


# --- Connexion / déconnexion ------------------------------------------------------

@bp.route("/connexion", methods=["GET", "POST"])
def connexion():
    suivant = request.values.get("suivant", "")
    if request.method == "POST":
        try:
            reponse = api.connexion(request.form.get("login", "").strip(),
                                    request.form.get("motDePasse", ""))
        except ErreurApi as erreur:
            if erreur.statut not in (400, 401):
                raise
            flash("Identifiant ou mot de passe incorrect", "danger")
        else:
            auth.ouvrir_session(reponse)
            flash(f"Bienvenue {reponse['utilisateur']['login']} !", "success")
            return redirect(auth.url_sure(suivant))
    return render_template("connexion.html", suivant=suivant,
                           login=request.form.get("login", ""))


@bp.post("/deconnexion")
def deconnexion():
    try:
        api.deconnexion()
    except ErreurApi:
        pass   # session déjà expirée côté API : on déconnecte quand même le navigateur
    auth.fermer_session()
    flash("Vous êtes déconnecté", "info")
    return redirect(url_for("catalogue.accueil"))


# --- Profil ------------------------------------------------------------------------------

@bp.route("/profil", methods=["GET", "POST"])
@auth.connexion_requise
def profil():
    erreurs = {}
    if request.method == "POST":
        nouveau = request.form.get("nouveauMotDePasse", "")
        if nouveau != request.form.get("confirmation", ""):
            erreurs["confirmation"] = "Les deux mots de passe ne correspondent pas"
        else:
            corps = {"motDePasseActuel": request.form.get("motDePasseActuel", ""),
                     "email": request.form.get("email", "").strip()}
            if nouveau:
                corps["nouveauMotDePasse"] = nouveau
            try:
                api.modifier_mon_profil(corps)
            except ErreurApi as erreur:
                if erreur.code == "MOT_DE_PASSE_INCORRECT":
                    erreurs["motDePasseActuel"] = erreur.message
                else:
                    erreurs = formulaires.erreurs_formulaire(erreur)
            else:
                flash("Profil mis à jour", "success")
                return redirect(url_for(".profil"))
    return render_template("profil.html", profil=api.mon_profil(), erreurs=erreurs)


# --- Prêts -------------------------------------------------------------------------------

@bp.get("/mes-prets")
@auth.connexion_requise
def mes_prets():
    moi = auth.utilisateur_courant()["id"]
    en_cours = api.lister_prets(statut="EN_COURS", utilisateurId=moi, taille=100)["elements"]
    historique = api.lister_prets(statut="RENDU", utilisateurId=moi,
                                  page=request.args.get("page"), taille=PRETS_PAR_PAGE)
    return render_template("mes_prets.html", en_cours=en_cours, historique=historique)


@bp.post("/supports/<support_id>/emprunter")
@auth.connexion_requise
def emprunter(support_id):
    film_id = request.form.get("film_id", "")
    try:
        pret = api.emprunter(support_id)
    except ErreurApi as erreur:
        if erreur.statut not in (400, 409):
            raise
        flash(erreur.message, "danger")
    else:
        flash(f"Emprunt enregistré : à rendre avant le {date_fr(pret['dateRetourPrevue'])}", "success")
        film_id = pret["film"]["id"]
    if film_id:
        return redirect(url_for("catalogue.film", film_id=film_id))
    return redirect(url_for(".mes_prets"))


@bp.post("/prets/<pret_id>/rendre")
@auth.connexion_requise
def rendre(pret_id):
    # Page de retour limitée à deux valeurs connues (pas de redirection arbitraire)
    retour = (url_for("admin.prets") if request.form.get("retour_vers") == "admin"
              else url_for(".mes_prets"))
    try:
        api.rendre(pret_id, formulaires.texte(request.form, "remarque"))
    except ErreurApi as erreur:
        if erreur.statut not in (403, 409):
            raise
        flash(erreur.message, "danger")
    else:
        flash("Retour enregistré, merci !", "success")
    return redirect(retour)


# --- Suivi personnel ---------------------------------------------------------------------

@bp.post("/films/<film_id>/suivi")
@auth.connexion_requise
def suivi(film_id):
    try:
        api.enregistrer_suivi(film_id, formulaires.suivi(request.form))
    except ErreurApi as erreur:
        if erreur.statut != 400:
            raise
        flash(f"Suivi non enregistré : {' '.join(erreur.details.values()) or erreur.message}", "danger")
    else:
        flash("Votre suivi a été enregistré", "success")
    return redirect(url_for("catalogue.film", film_id=film_id) + "#mon-suivi")
