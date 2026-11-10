"""Routes du site web, regroupées en trois Blueprints :
- catalogue : pages publiques (accueil, catalogue, fiche film, personne)
- compte    : connexion, profil, prêts et suivis de l'utilisateur connecté
- admin     : gestion des films, supports, personnes, prêts et comptes (/admin/...)
"""
from routes import admin, catalogue, compte

BLUEPRINTS = [catalogue.bp, compte.bp, admin.bp]
