# Crypto & Monnaie Monitoring Platform

Une plateforme Django moderne pour le suivi des cryptomonnaies, devises FIAT et matières premières tokenisées utilisant l'API Binance.

## Fonctionnalités

- **Page d'atterrissage** : Sélection du profil utilisateur (investisseur débutant, trader confirmé, analyste)
- **Page d'accueil** : Carrousel des paires populaires et watchlist personnalisée
- **Recherche avancée** : Filtres par type, prix, variation, volume et capitalisation
- **Pages détaillées** : Informations complètes sur chaque paire de trading
- **Watchlist & Portfolio** : Suivi des actifs et simulation de portefeuille
- **Gestion de session** : Sauvegarde des préférences utilisateur

## Installation et Lancement

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Connexion Internet (pour l'API Binance)

### Installation rapide

#### Option 1 : Lancement automatique (Windows)

1. Double-cliquez sur le fichier `LANCER_APPLICATION.bat`
2. Le serveur démarre automatiquement
3. Ouvrez votre navigateur à http://localhost:8000

#### Option 2 : Ligne de commande

**1. Naviguer vers le dossier du projet**

```bash
cd "chemin/vers/Projet groupe Django monnaie"
```

**2. Installer les dépendances**

```bash
pip install -r requirements.txt
```

**3. Créer les migrations de base de données**

```bash
python manage.py makemigrations accounts watchlist
python manage.py migrate
```

**4. (Optionnel) Créer un superutilisateur pour l'admin**

```bash
python manage.py createsuperuser
```

**5. Lancer le serveur de développement**

```bash
python manage.py runserver
```

Le serveur démarre sur `http://localhost:8000` ou `http://127.0.0.1:8000`

**6. Accéder à l'application**
Ouvrez votre navigateur et allez à :

- **Page d'accueil** : http://localhost:8000
- **Interface admin** : http://localhost:8000/admin (si superutilisateur créé)

### Arrêter le serveur

Dans le terminal où le serveur tourne, appuyez sur `Ctrl + C` (Windows/Linux) ou `Ctrl + Break` (Windows)

### Problèmes courants

**[ERREUR] Erreur "No module named 'django'"**

```bash
pip install -r requirements.txt
```

**[ERREUR] Erreur "Port already in use"**

```bash
python manage.py runserver 8080
# Puis allez sur http://localhost:8080
```

**[ERREUR] Erreurs de migration**

```bash
python manage.py makemigrations
python manage.py migrate --run-syncdb
```

## Structure du Projet

- `crypto_monitor/` : Configuration principale du projet Django
- `landing/` : Page d'atterrissage et sélection de profil
- `home/` : Page d'accueil avec carrousel et watchlist
- `search/` : Recherche et filtrage des paires
- `pairs/` : Pages détaillées des paires de trading
- `watchlist/` : Gestion de la watchlist et du portefeuille
- `accounts/` : Gestion des utilisateurs et sessions
- `api_services/` : Services d'intégration avec l'API Binance

## API Utilisée

Binance Spot API: https://binance-docs.github.io/apidocs/spot/en/

## Technologies

- Django 4.2
- Bootstrap 5
- **TradingView Advanced Charts** (graphiques professionnels identiques à Binance)
- API REST Binance (données en temps réel)
- Sessions Django pour la gestion utilisateur

## Graphiques Professionnels TradingView

Notre application contient maintenant les memes charts que sur binance soit celles de Trading view via la fonctionalitée widget

**10+ types de graphiques** : Bougies japonaises, Heiken Ashi, lignes, etc.
**100+ indicateurs techniques** : EMA, Double EMA, Triple EMA, Bollinger Bands, MACD, RSI, etc.
**Outils de dessin avancés** : Fibonacci, lignes de tendance, support/résistance
**Tous les timeframes** : De la seconde au mois
**Données temps réel de Binance**
