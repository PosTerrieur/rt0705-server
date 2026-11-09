"""Tiers présentation de la vidéothèque - version de test des conteneurs"""
from flask import Flask, redirect, url_for

from pages_test import pages_test

app = Flask(__name__)
app.json.ensure_ascii = False   # accents lisibles dans le filtre Jinja tojson
app.json.sort_keys = False

app.register_blueprint(pages_test)


@app.get("/")
def accueil():
    return redirect(url_for("pages_test.simple"))
