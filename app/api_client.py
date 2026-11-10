"""Accès au tiers données : seul module du serveur web qui appelle l'API"""
import os

import requests
from flask import session

API_URL = os.environ.get("API_URL", "http://api:5001/api")
DELAI_SECONDES = 5


class ErreurApi(Exception):
    """Erreur renvoyée par l'API (ou API injoignable), avec le format commun"""

    def __init__(self, statut, code, message, details=None):
        super().__init__(message)
        self.statut = statut
        self.code = code
        self.message = message
        self.details = details or {}


def _appel(methode, chemin, corps=None, params=None, jeton=None, delai=DELAI_SECONDES):
    """Envoie la requête et renvoie le JSON décodé (None pour une réponse 204)"""
    entetes = {}
    jeton = jeton or session.get("jeton")
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    # On n'envoie pas les paramètres vides (filtres non renseignés)
    if params:
        params = {cle: valeur for cle, valeur in params.items() if valeur not in (None, "")}

    try:
        reponse = requests.request(methode, API_URL + chemin, json=corps, params=params,
                                   headers=entetes, timeout=delai)
    except requests.RequestException as erreur:
        raise ErreurApi(503, "API_INJOIGNABLE",
                        "Le service de données est momentanément indisponible") from erreur

    if reponse.status_code == 204:
        return None
    try:
        donnees = reponse.json()
    except ValueError:
        donnees = {}
    if not reponse.ok:
        erreur = donnees.get("erreur", {})
        raise ErreurApi(reponse.status_code, erreur.get("code", "ERREUR_API"),
                        erreur.get("message", f"Erreur {reponse.status_code}"),
                        erreur.get("details"))
    return donnees


# --- Sessions -------------------------------------------------------------------

def connexion(login, mot_de_passe):
    return _appel("POST", "/sessions", {"login": login, "motDePasse": mot_de_passe})


def deconnexion():
    return _appel("DELETE", "/sessions/current")


# --- Profil et comptes -------------------------------------------------------------

def mon_profil():
    return _appel("GET", "/utilisateurs/me")


def modifier_mon_profil(corps):
    return _appel("PATCH", "/utilisateurs/me", corps)


def lister_utilisateurs(actif=None):
    return _appel("GET", "/utilisateurs", params={"actif": actif})


def obtenir_utilisateur(utilisateur_id):
    return _appel("GET", f"/utilisateurs/{utilisateur_id}")


def creer_utilisateur(corps):
    return _appel("POST", "/utilisateurs", corps)


def modifier_utilisateur(utilisateur_id, corps):
    return _appel("PATCH", f"/utilisateurs/{utilisateur_id}", corps)


# --- Films --------------------------------------------------------------------------

def rechercher_films(**criteres):
    """criteres : q, genre, annee, realisateur, acteur, type, disponible, tri, ordre, page, taille"""
    return _appel("GET", "/films", params=criteres)


def obtenir_film(film_id):
    return _appel("GET", f"/films/{film_id}")


def creer_film(corps):
    return _appel("POST", "/films", corps)


def modifier_film(film_id, corps):
    return _appel("PATCH", f"/films/{film_id}", corps)


def supprimer_film(film_id):
    return _appel("DELETE", f"/films/{film_id}")


# --- Supports -------------------------------------------------------------------------

def obtenir_support(support_id):
    return _appel("GET", f"/supports/{support_id}")


def creer_support(film_id, corps):
    return _appel("POST", f"/films/{film_id}/supports", corps)


def modifier_support(support_id, corps):
    return _appel("PATCH", f"/supports/{support_id}", corps)


def supprimer_support(support_id):
    return _appel("DELETE", f"/supports/{support_id}")


# --- Personnes ------------------------------------------------------------------------

def obtenir_personne(personne_id):
    return _appel("GET", f"/personnes/{personne_id}")


def renommer_personne(personne_id, nom):
    return _appel("PATCH", f"/personnes/{personne_id}", {"nom": nom})


# --- Prêts ------------------------------------------------------------------------------

def emprunter(support_id):
    return _appel("POST", "/prets", {"supportId": support_id})


def lister_prets(**filtres):
    """filtres : statut, enRetard, utilisateurId, page, taille"""
    return _appel("GET", "/prets", params=filtres)


def rendre(pret_id, remarque=None):
    return _appel("POST", f"/prets/{pret_id}/retour", {"remarque": remarque})


# --- Suivis personnels ---------------------------------------------------------------------

def mon_suivi(film_id):
    """Suivi de l'utilisateur connecté pour ce film, ou None s'il n'en a pas encore"""
    try:
        return _appel("GET", f"/utilisateurs/me/suivis/{film_id}")
    except ErreurApi as erreur:
        if erreur.statut == 404:
            return None
        raise


def enregistrer_suivi(film_id, corps):
    return _appel("PUT", f"/utilisateurs/me/suivis/{film_id}", corps)


# --- Métadonnées externes (bonus F15) ----------------------------------------------------

def importer_metadonnees(titre, annee=None):
    """Proposition de fiche depuis TMDb"""
    return _appel("GET", "/metadonnees", params={"titre": titre, "annee": annee}, delai=15)
