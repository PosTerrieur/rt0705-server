"""Accès au tiers données : seul module du serveur web qui appelle l'API"""
import os

import requests

API_URL = os.environ.get("API_URL", "http://api:5001/api")
DELAI_SECONDES = 5


class ErreurApi(Exception):
    """L'API est injoignable ou a renvoyé une erreur"""


def get(chemin):
    """Envoie un GET à l'API et renvoie le JSON décodé"""
    url = f"{API_URL}{chemin}"
    try:
        reponse = requests.get(url, timeout=DELAI_SECONDES)
    except requests.RequestException as e:
        raise ErreurApi(f"API injoignable ({url}) : {e}") from e

    try:
        donnees = reponse.json()
    except ValueError:
        donnees = {}

    if not reponse.ok:
        message = donnees.get("erreur", {}).get("message", "erreur inconnue")
        raise ErreurApi(f"L'API a répondu {reponse.status_code} : {message}")
    return donnees
