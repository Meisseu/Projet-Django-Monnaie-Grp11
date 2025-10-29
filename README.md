# Crypto & Monnaie Monitoring Platform

Une plateforme Django moderne pour le suivi des cryptomonnaies, devises FIAT et matières premières tokenisées utilisant l'API Binance.

## Fonctionnalités

- **Page d'atterrissage** : Sélection du profil utilisateur (investisseur débutant, trader confirmé, analyste)
- **Page d'accueil** : Carrousel des paires populaires et watchlist personnalisée
- **Recherche avancée** : Filtres par type, prix, variation, volume et capitalisation
- **Pages détaillées** : Informations complètes sur chaque paire de trading
- **Watchlist & Portfolio** : Suivi des actifs et simulation de portefeuille
- **Gestion de session** : Sauvegarde des préférences utilisateur

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Appliquer les migrations :
```bash
python manage.py migrate
```

3. Créer un superutilisateur (optionnel) :
```bash
python manage.py createsuperuser
```

4. Lancer le serveur :
```bash
python manage.py runserver
```

5. Accéder à l'application :
```
http://localhost:8000
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
- Chart.js pour les graphiques
- API REST Binance
- Sessions Django pour la gestion utilisateur

