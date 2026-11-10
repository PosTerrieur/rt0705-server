# Vidéothèque RT0705 : site web (tiers présentation)

Site web de la vidéothèque partagée, en Flask + Jinja + Bootstrap. C'est le **tiers présentation** de l'architecture 3 tiers :

```text
Navigateur  ──HTML──▶  serveur (ce dépôt)  ──HTTP + JSON──▶  API (dépôt API/)  ──▶  fichiers JSON
  client                présentation                          données
```

- **Le site ne lit et n'écrit jamais les données.** Toute information passe par une requête HTTP vers l'API (`http://api:5001/api/...`), envoyée par un seul module : `app/api_client.py`.
- **Le volume de données n'est monté que dans le conteneur de l'API** : le site ne peut physiquement pas lire le fichier JSON.
- **Seul port publié de toute l'application : 8080.**

* * *

## Lancer toute l'application (création coordonnée)

### Prérequis

- Docker et **Docker Compose 2.20 ou plus récent** (`docker compose version`), nécessaire pour l'instruction `include`.
- Les deux dépôts **côte à côte** :

```text
rt0705/
├── serveur/     ce dépôt
└── API/         dépôt de l'API
```

### Première installation

```bash
# 1. Réseau Docker commun (une seule fois)
docker network create videotheque_net

# 2. Clé de signature des sessions (fichier .env non versionné)
cd serveur
cp .env.exemple .env
sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')/" .env

# 3. Facultatif : clé TMDb pour l'import de fiches, dans le .env de l'API
cp ../API/.env.exemple ../API/.env        # puis renseigner TMDB_API_KEY
```

### Lancement : une seule commande, depuis `serveur/`

```bash
docker compose up -d --build
```

Grâce à `include`, cette commande construit et démarre **les deux conteneurs**, dans le bon ordre : le site attend que l'API soit « healthy » (healthcheck sur `/api/sante`).

```text
 ✔ Container videotheque-api  Healthy
 ✔ Container videotheque-web  Started
```

Ouvre ensuite **http://<IP_DE_LA_VM>:8080/**, ou http://localhost:8080/ avec le transfert de port de VSCode (onglet **Ports**).

```bash
docker compose ps          # état des deux conteneurs
docker compose logs -f     # journaux des deux conteneurs
docker compose down        # arrêt des deux conteneurs (les données sont conservées)
```

> **Docker Compose plus ancien que 2.20** : supprimer les blocs `include` et `depends_on` de `docker-compose.yml`, puis lancer `docker compose up -d` dans `API/`, puis `docker compose up -d --build` dans `serveur/`.

* * *

## Comptes de démonstration

Mot de passe commun : **`videotheque`**

| Login | Rôle | Pour tester |
| --- | --- | --- |
| `camille` | Administrateur | Ajout et modification de films et de supports, import TMDb, supervision des prêts, gestion des comptes |
| `lucas` | Membre | Emprunt, retour, notes et avis. A un prêt en cours (*Inception*) |
| `ines` | Membre | A un prêt **en retard** (*Amélie*) |
| `theo` | Membre désactivé | La connexion doit être refusée |

* * *

## Pages

| Page | Accès | Contenu |
| --- | --- | --- |
| `/` | Tous | Accueil, recherche, derniers ajouts |
| `/films` | Tous | Catalogue : filtres (titre, genre, année, réalisateur, acteur, support, disponibilité), tri, pagination |
| `/films/<id>` | Tous | Fiche : note moyenne en haut, supports et emprunt, mon suivi, avis des membres en bas |
| `/personnes/<id>` | Tous | Filmographie d'un réalisateur ou acteur |
| `/connexion`, `/profil` | Visiteur / membre | Connexion, modification de l'email et du mot de passe |
| `/mes-prets` | Membre | Prêts en cours (bouton de retour), historique |
| `/admin/films/nouveau` | Admin | Ajout d'un film, avec **préremplissage depuis TMDb** |
| `/admin/prets` | Admin | Supervision : filtres, retards, clôture d'un prêt |
| `/admin/utilisateurs` | Admin | Création, modification, désactivation des comptes |

* * *

## Configuration

Fichier `.env` (non versionné), modèle dans `.env.exemple` :

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `SECRET_KEY` | valeur de développement | Signature du cookie de session. **À définir** avec une valeur aléatoire |
| `FLASK_DEBUG` | `0` | `1` : rechargement automatique du code et page de débogage (développement uniquement) |

`API_URL` (`http://api:5001/api`) est fixée dans `docker-compose.yml` : c'est le nom du service de l'API sur le réseau Docker.

* * *

## Choix techniques

- **Rendu côté serveur** : chaque page est une route Flask qui appelle l'API, puis remplit un template Jinja. Le JavaScript se limite à une confirmation avant suppression.
- **Session** : la connexion appelle `POST /api/sessions`. Le jeton reçu est stocké dans la session Flask (cookie **signé**, **HttpOnly**, **SameSite=Lax**) puis envoyé à chaque appel dans `Authorization: Bearer`. Le rôle stocké en session ne sert qu'à **afficher** les menus : les droits sont vérifiés par l'API. Si l'API répond 401 (jeton expiré, compte désactivé), le site renvoie vers la connexion.
- **Pas de duplication des règles métier** : les formulaires sont convertis en JSON (`formulaires.py`), et c'est l'API qui valide. Ses erreurs s'affichent sous chaque champ.
- **Post / Redirect / Get** : chaque action (emprunt, retour, suppression...) redirige après traitement, avec un message. Rafraîchir la page ne répète pas l'action.
- **Bootstrap 5.3** est chargé depuis un CDN par le navigateur : le conteneur n'a pas besoin d'accès à Internet.

* * *

## Arborescence

```text
serveur/
├── Dockerfile              image Flask générique (identique à celle de l'API)
├── docker-compose.yml      service web + include de ../API/docker-compose.yml
├── requirements.txt        Flask, requests
├── .env.exemple
└── app/                    code (monté sur /app)
    ├── app.py              création de l'app, session, gestion des erreurs de l'API
    ├── api_client.py       SEUL module qui appelle l'API
    ├── auth.py             session et contrôles de surface
    ├── formulaires.py      formulaires HTML → JSON
    ├── affichage.py        filtres Jinja (dates, durées, libellés, étoiles)
    ├── routes/             catalogue.py, compte.py, admin.py
    ├── templates/          base.html, macros.html, 8 pages + erreur.html, admin/ (6 pages)
    └── static/             css/style.css, js/confirmation.js
```

## Dépannage

| Symptôme | Cause et solution |
| --- | --- |
| `network videotheque_net declared as external, but could not be found` | Réseau non créé : `docker network create videotheque_net` |
| `Conflict. The container name "/videotheque-api" is already in use` | L'API a déjà été lancée seule depuis `API/` : `docker compose down` dans `API/`, puis relancer ici |
| Page « Service indisponible » | L'API ne répond pas : `docker compose ps` et `docker compose logs api` |
| Page inaccessible depuis le navigateur | VPN ou filtrage : utiliser le transfert du port 8080 dans VSCode |
| « Import impossible » sur l'ajout de film | Pas de `TMDB_API_KEY` dans `API/.env`, ou TMDb injoignable. La saisie manuelle reste possible |

Données de films et affiches importées : ce produit utilise l'API TMDb, sans être approuvé ni certifié par TMDb.
