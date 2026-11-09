"""Pages de test des conteneurs"""
from flask import Blueprint, render_template, request

import api_client

pages_test = Blueprint("pages_test", __name__, url_prefix="/test")

NOTES_POSSIBLES = [str(n) for n in range(6)]   # "0" à "5"


# --- Test 1 : page HTML simple ---------------------------------------------

@pages_test.get("/simple")
def simple():
    return render_template("simple.html")


# --- Test 2 : formulaire + page de traitement -------------------------------

@pages_test.get("/formulaire")
def formulaire():
    return render_template("formulaire.html", valeurs={}, erreurs={},
                           notes=NOTES_POSSIBLES)


@pages_test.post("/formulaire/traitement")
def traitement_formulaire():
    valeurs = {
        "nom": request.form.get("nom", "").strip(),
        "film": request.form.get("film", "").strip(),
        "note": request.form.get("note", ""),
        "vu": "vu" in request.form,          # case à cocher : présente ou absente
    }
    erreurs = valider_formulaire(valeurs)

    if erreurs:
        # On réaffiche le formulaire avec les messages et les valeurs saisies
        return render_template("formulaire.html", valeurs=valeurs, erreurs=erreurs,
                               notes=NOTES_POSSIBLES), 400

    valeurs["note"] = int(valeurs["note"])
    return render_template("formulaire_resultat.html", **valeurs)


def valider_formulaire(valeurs):
    """Renvoie un dictionnaire {champ: message} des erreurs (vide si tout va bien)."""
    erreurs = {}
    if not valeurs["nom"]:
        erreurs["nom"] = "Le nom est obligatoire."
    if not valeurs["film"]:
        erreurs["film"] = "Indiquez un film."
    if valeurs["note"] not in NOTES_POSSIBLES:
        erreurs["note"] = "La note doit être un entier entre 0 et 5."
    return erreurs


# --- Test 3 : template Jinja alimenté par le fichier JSON (via l'API) -------

@pages_test.get("/json")
def json_test():
    try:
        donnees = api_client.get("/test/videotheque")
    except api_client.ErreurApi as e:
        return render_template("json_test.html", donnees=None, erreur=str(e)), 502
    return render_template("json_test.html", donnees=donnees, erreur=None,
                           source=api_client.API_URL)
