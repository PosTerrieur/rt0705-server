"""Filtres Jinja pour l'affichage : dates, durées, libellés, étoiles"""
from datetime import date

LIBELLES = {
    # Types et catégories de supports
    "DVD": "DVD", "BLU_RAY": "Blu-ray", "BLU_RAY_4K": "Blu-ray 4K", "VHS": "VHS",
    "NUMERIQUE": "Numérique", "PHYSIQUE": "Physique",
    # États
    "NEUF": "Neuf", "BON": "Bon état", "USE": "Usé", "ENDOMMAGE": "Endommagé", "PERDU": "Perdu",
    # Prêts
    "EN_COURS": "En cours", "RENDU": "Rendu",
    # Rôles
    "MEMBRE": "Membre", "ADMIN": "Administrateur",
    "REALISATEUR": "Réalisation", "ACTEUR": "Interprétation",
}


def libelle(valeur):
    """Libellé lisible d'une valeur d'énumération : BLU_RAY_4K -> « Blu-ray 4K »"""
    return LIBELLES.get(valeur, valeur)


def date_fr(valeur):
    """2026-11-06 -> 06/11/2026"""
    if not valeur:
        return ""
    return date.fromisoformat(valeur[:10]).strftime("%d/%m/%Y")


def duree(minutes):
    """148 -> « 2 h 28 »"""
    if not minutes:
        return ""
    return f"{minutes // 60} h {minutes % 60:02d}"


def etoiles(note):
    """3.6 -> « ★★★★☆ »
    (round() de Python arrondit au pair le plus proche : round(4.5) vaut 4)
    """
    if note is None:
        return ""
    pleines = int(note + 0.5)
    return "★" * pleines + "☆" * (5 - pleines)


FILTRES = {"libelle": libelle, "date_fr": date_fr, "duree": duree, "etoiles": etoiles}
