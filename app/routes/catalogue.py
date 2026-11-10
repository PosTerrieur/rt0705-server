"""Pages publiques : accueil, catalogue, fiche film, personne (F04, F05, F08, F09, F16)"""
from flask import Blueprint, flash, render_template, request

import api_client as api
import auth
from api_client import ErreurApi

bp = Blueprint("catalogue", __name__)

FILTRES = ("q", "genre", "annee", "realisateur", "acteur", "type", "disponible", "tri", "ordre", "page")
TYPES_SUPPORT = ("DVD", "BLU_RAY", "BLU_RAY_4K", "VHS", "NUMERIQUE")
TRIS = {"titre": "Titre", "annee": "Année", "dateAjout": "Date d'ajout", "note": "Note"}
FILMS_PAR_PAGE = 12


@bp.get("/")
def accueil():
    derniers = api.rechercher_films(tri="dateAjout", ordre="desc", taille=8)
    return render_template("index.html", films=derniers["elements"])


@bp.get("/films")
def catalogue():
    # Les filtres sont transmis tels quels à l'API qui les valide
    criteres = {cle: request.args.get(cle) for cle in FILTRES}
    try:
        resultat = api.rechercher_films(**criteres, taille=FILMS_PAR_PAGE)
    except ErreurApi as erreur:
        if erreur.statut != 400:
            raise
        flash(f"Recherche invalide : {erreur.message} {' '.join(erreur.details.values())}", "danger")
        resultat = {"elements": [], "pagination": {"page": 1, "taille": FILMS_PAR_PAGE, "total": 0}}
    return render_template("catalogue.html", resultat=resultat, criteres=request.args,
                           types=TYPES_SUPPORT, tris=TRIS)


@bp.get("/films/<film_id>")
def film(film_id):
    fiche = api.obtenir_film(film_id)
    suivi = api.mon_suivi(film_id) if auth.utilisateur_courant() else None
    return render_template("film.html", film=fiche, suivi=suivi)


@bp.get("/personnes/<personne_id>")
def personne(personne_id):
    return render_template("personne.html", personne=api.obtenir_personne(personne_id))
