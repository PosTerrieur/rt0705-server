"""Administration (/admin/...) : films, supports, personnes, prêts et comptes (F03, F06, F07, F13, F17)"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import api_client as api
import formulaires
from api_client import ErreurApi
from auth import admin_requis

bp = Blueprint("admin", __name__, url_prefix="/admin")

CATEGORIES = ("PHYSIQUE", "NUMERIQUE")
TYPES_PHYSIQUES = ("DVD", "BLU_RAY", "BLU_RAY_4K", "VHS")
ETATS = ("NEUF", "BON", "USE", "ENDOMMAGE", "PERDU")
ROLES = ("MEMBRE", "ADMIN")
PRETS_PAR_PAGE = 20


# --- Films (F06) ---------------------------------------------------------------------

def _proposition_tmdb(titre, annee):
    """Valeurs du formulaire préremplies depuis TMDb (bonus F15)"""
    try:
        proposition = api.importer_metadonnees(titre, annee)
    except ErreurApi as erreur:
        if erreur.statut not in (400, 404, 503):
            raise
        flash(f"Import impossible : {erreur.message} Vous pouvez saisir la fiche manuellement", "warning")
        return {"titre": titre, "annee": annee}
    flash("Fiche préremplie depuis TMDb : vérifiez les informations, puis enregistrez", "info")
    return formulaires.film_vers_formulaire(proposition)


@bp.route("/films/nouveau", methods=["GET", "POST"])
@admin_requis
def film_nouveau():
    valeurs, erreurs = {}, {}
    titre_import = request.args.get("import_titre", "").strip()
    if request.method == "GET" and titre_import:
        valeurs = _proposition_tmdb(titre_import, request.args.get("import_annee", "").strip() or None)
    if request.method == "POST":
        valeurs = request.form.to_dict()
        try:
            film = api.creer_film(formulaires.film(request.form))
        except ErreurApi as erreur:
            erreurs = formulaires.erreurs_formulaire(erreur)
        else:
            flash(f"Film « {film['titre']} » ajouté, ajoutez-lui maintenant un support", "success")
            return redirect(url_for("catalogue.film", film_id=film["id"]))
    return render_template("admin/film_form.html", film=None, valeurs=valeurs, erreurs=erreurs)


@bp.route("/films/<film_id>/modifier", methods=["GET", "POST"])
@admin_requis
def film_modifier(film_id):
    film = api.obtenir_film(film_id)
    valeurs, erreurs = formulaires.film_vers_formulaire(film), {}
    if request.method == "POST":
        valeurs = request.form.to_dict()
        try:
            api.modifier_film(film_id, formulaires.film(request.form))
        except ErreurApi as erreur:
            erreurs = formulaires.erreurs_formulaire(erreur)
        else:
            flash("Film modifié", "success")
            return redirect(url_for("catalogue.film", film_id=film_id))
    return render_template("admin/film_form.html", film=film, valeurs=valeurs, erreurs=erreurs)


@bp.post("/films/<film_id>/supprimer")
@admin_requis
def film_supprimer(film_id):
    try:
        api.supprimer_film(film_id)
    except ErreurApi as erreur:
        if erreur.statut != 409:
            raise
        flash(f"Suppression impossible : {erreur.message}", "danger")
        return redirect(url_for("catalogue.film", film_id=film_id))
    flash("Film supprimé, ainsi que ses supports et son historique", "success")
    return redirect(url_for("catalogue.catalogue"))


# --- Supports (F07) ----------------------------------------------------------------

@bp.route("/films/<film_id>/supports/nouveau", methods=["GET", "POST"])
@admin_requis
def support_nouveau(film_id):
    categorie = request.values.get("categorie", "PHYSIQUE")
    if categorie not in CATEGORIES:
        abort(404)
    film = api.obtenir_film(film_id)
    valeurs, erreurs = {"etat": "BON"}, {}
    if request.method == "POST":
        valeurs = request.form.to_dict()
        corps = {"categorie": categorie, **formulaires.support(request.form, categorie)}
        try:
            api.creer_support(film_id, corps)
        except ErreurApi as erreur:
            erreurs = formulaires.erreurs_formulaire(erreur)
        else:
            flash("Support ajouté", "success")
            return redirect(url_for("catalogue.film", film_id=film_id))
    return render_template("admin/support_form.html", film=film, support=None, categorie=categorie,
                           valeurs=valeurs, erreurs=erreurs, types=TYPES_PHYSIQUES, etats=ETATS)


@bp.route("/supports/<support_id>/modifier", methods=["GET", "POST"])
@admin_requis
def support_modifier(support_id):
    support = api.obtenir_support(support_id)
    film = api.obtenir_film(support["filmId"])
    valeurs, erreurs = support, {}
    if request.method == "POST":
        valeurs = request.form.to_dict()
        try:
            api.modifier_support(support_id, formulaires.support(request.form, support["categorie"]))
        except ErreurApi as erreur:
            erreurs = formulaires.erreurs_formulaire(erreur)
        else:
            flash("Support modifié", "success")
            return redirect(url_for("catalogue.film", film_id=film["id"]))
    return render_template("admin/support_form.html", film=film, support=support,
                           categorie=support["categorie"], valeurs=valeurs, erreurs=erreurs,
                           types=TYPES_PHYSIQUES, etats=ETATS)


@bp.post("/supports/<support_id>/supprimer")
@admin_requis
def support_supprimer(support_id):
    film_id = api.obtenir_support(support_id)["filmId"]
    try:
        api.supprimer_support(support_id)
    except ErreurApi as erreur:
        if erreur.statut != 409:
            raise
        flash(f"Suppression impossible : {erreur.message}", "danger")
    else:
        flash("Support supprimé", "success")
    return redirect(url_for("catalogue.film", film_id=film_id))


# --- Personnes (F17) ----------------------------------------------------------------

@bp.route("/personnes/<personne_id>/modifier", methods=["GET", "POST"])
@admin_requis
def personne_modifier(personne_id):
    personne = api.obtenir_personne(personne_id)
    valeurs, erreurs = {"nom": personne["nom"]}, {}
    if request.method == "POST":
        valeurs = request.form.to_dict()
        try:
            api.renommer_personne(personne_id, request.form.get("nom", "").strip())
        except ErreurApi as erreur:
            erreurs = formulaires.erreurs_formulaire(erreur)
        else:
            flash("Nom corrigé sur tous les films de cette personne", "success")
            return redirect(url_for("catalogue.personne", personne_id=personne_id))
    return render_template("admin/personne_form.html", personne=personne,
                           valeurs=valeurs, erreurs=erreurs)


# --- Supervision des prêts (F13) ---------------------------------------------------------

@bp.get("/prets")
@admin_requis
def prets():
    filtres = {
        "statut": request.args.get("statut"),
        "enRetard": "true" if request.args.get("enRetard") else None,
        "utilisateurId": request.args.get("utilisateurId"),
        "page": request.args.get("page"),
    }
    resultat = api.lister_prets(**filtres, taille=PRETS_PAR_PAGE)
    utilisateurs = api.lister_utilisateurs()
    logins = {u["id"]: u["login"] for u in utilisateurs}
    return render_template("admin/prets.html", resultat=resultat, utilisateurs=utilisateurs,
                           logins=logins, filtres=request.args)


# --- Comptes (F03) -------------------------------------------------------------------------

@bp.get("/utilisateurs")
@admin_requis
def utilisateurs():
    return render_template("admin/utilisateurs.html", utilisateurs=api.lister_utilisateurs())


@bp.route("/utilisateurs/nouveau", methods=["GET", "POST"])
@admin_requis
def utilisateur_nouveau():
    valeurs, erreurs = {"role": "MEMBRE"}, {}
    if request.method == "POST":
        valeurs = request.form.to_dict()
        try:
            compte = api.creer_utilisateur(formulaires.nouvel_utilisateur(request.form))
        except ErreurApi as erreur:
            erreurs = formulaires.erreurs_formulaire(erreur)
        else:
            flash(f"Compte « {compte['login']} » créé.", "success")
            return redirect(url_for(".utilisateurs"))
    return render_template("admin/utilisateur_form.html", compte=None, valeurs=valeurs,
                           erreurs=erreurs, roles=ROLES)


@bp.route("/utilisateurs/<utilisateur_id>/modifier", methods=["GET", "POST"])
@admin_requis
def utilisateur_modifier(utilisateur_id):
    compte = api.obtenir_utilisateur(utilisateur_id)
    valeurs, erreurs = compte, {}
    if request.method == "POST":
        valeurs = request.form.to_dict()
        try:
            api.modifier_utilisateur(utilisateur_id, formulaires.modification_utilisateur(request.form))
        except ErreurApi as erreur:
            erreurs = formulaires.erreurs_formulaire(erreur)
        else:
            flash(f"Compte « {compte['login']} » modifié.", "success")
            return redirect(url_for(".utilisateurs"))
    return render_template("admin/utilisateur_form.html", compte=compte, valeurs=valeurs,
                           erreurs=erreurs, roles=ROLES)


@bp.post("/utilisateurs/<utilisateur_id>/activation")
@admin_requis
def utilisateur_activation(utilisateur_id):
    actif = request.form.get("actif") == "1"
    try:
        compte = api.modifier_utilisateur(utilisateur_id, {"actif": actif})
    except ErreurApi as erreur:
        if erreur.statut != 409:
            raise
        flash(erreur.message, "danger")
    else:
        etat = "réactivé" if actif else "désactivé (ses sessions sont fermées)"
        flash(f"Compte « {compte['login']} » {etat}.", "success")
    return redirect(url_for(".utilisateurs"))
