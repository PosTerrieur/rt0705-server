"""Conversion des formulaires HTML en corps JSON pour l'API"""
from flask import flash

from api_client import ErreurApi


def erreurs_formulaire(erreur):
    """Traduit une erreur de l'API en erreurs à afficher sous les champs du formulaire"""
    if not isinstance(erreur, ErreurApi) or erreur.statut not in (400, 409):
        raise erreur
    if erreur.statut == 400 and erreur.details:
        flash("Le formulaire contient des erreurs : corrigez les champs signalés", "danger")
        return erreur.details
    flash(erreur.message, "danger")
    return {}


def texte(formulaire, champ):
    """Texte nettoyé, ou None si le champ est vide (champ facultatif)"""
    valeur = formulaire.get(champ, "").strip()
    return valeur or None


def entier(formulaire, champ):
    valeur = formulaire.get(champ, "").strip()
    if not valeur:
        return None
    try:
        return int(valeur)
    except ValueError:
        return valeur


def nombre(formulaire, champ):
    valeur = formulaire.get(champ, "").strip().replace(",", ".")
    if not valeur:
        return None
    try:
        return float(valeur)
    except ValueError:
        return valeur


def case_cochee(formulaire, champ):
    return champ in formulaire


def liste_virgules(formulaire, champ):
    """« Drame, Comédie » -> ["Drame", "Comédie"]"""
    return [e.strip() for e in formulaire.get(champ, "").split(",") if e.strip()]


def liste_lignes(formulaire, champ):
    """Zone de texte avec un élément par ligne -> liste"""
    return [e.strip() for e in formulaire.get(champ, "").splitlines() if e.strip()]


# --- Formulaires de l'application -----------------------------------------------------

def film(formulaire):
    corps = {
        "titre": formulaire.get("titre", "").strip(),
        "titreOriginal": texte(formulaire, "titreOriginal"),
        "annee": entier(formulaire, "annee"),
        "dureeMinutes": entier(formulaire, "dureeMinutes"),
        "synopsis": texte(formulaire, "synopsis"),
        "genres": liste_virgules(formulaire, "genres"),
        "langueOriginale": texte(formulaire, "langueOriginale"),
        "afficheUrl": texte(formulaire, "afficheUrl"),
        "realisateurs": liste_lignes(formulaire, "realisateurs"),
        "acteurs": liste_lignes(formulaire, "acteurs"),
    }

    for champ in ("annee", "dureeMinutes"):
        if corps[champ] is None:
            del corps[champ]
    return corps


def film_vers_formulaire(fiche):
    """Fiche renvoyée par l'API -> valeurs pour préremplir le formulaire"""
    return {
        **fiche,
        "genres": ", ".join(fiche["genres"]),
        "realisateurs": "\n".join(p["nom"] for p in fiche["realisateurs"]),
        "acteurs": "\n".join(p["nom"] for p in fiche["acteurs"]),
    }


def support(formulaire, categorie):
    """Seuls les champs de la catégorie concernée sont envoyés"""
    corps = {
        "dateAcquisition": texte(formulaire, "dateAcquisition"),
        "commentaire": texte(formulaire, "commentaire"),
    }
    if categorie == "PHYSIQUE":
        corps.update(type=formulaire.get("type"), etat=formulaire.get("etat"),
                     emplacement=texte(formulaire, "emplacement"))
    else:
        corps.update(format=formulaire.get("format", "").strip(),
                     resolution=texte(formulaire, "resolution"),
                     chemin=formulaire.get("chemin", "").strip(),
                     tailleGo=nombre(formulaire, "tailleGo"))
    return corps


def suivi(formulaire):
    return {
        "vu": case_cochee(formulaire, "vu"),
        "note": entier(formulaire, "note"),
        "commentaire": texte(formulaire, "commentaire"),
    }


def nouvel_utilisateur(formulaire):
    return {
        "login": formulaire.get("login", "").strip(),
        "email": formulaire.get("email", "").strip(),
        "motDePasse": formulaire.get("motDePasse", ""),
        "role": formulaire.get("role", "MEMBRE"),
    }


def modification_utilisateur(formulaire):
    corps = {"email": formulaire.get("email", "").strip(), "role": formulaire.get("role")}
    if formulaire.get("motDePasse"):
        corps["motDePasse"] = formulaire["motDePasse"]
    return corps
