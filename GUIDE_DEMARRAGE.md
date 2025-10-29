# Guide de Démarrage Rapide - Crypto Monitor

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Connexion Internet (pour l'API Binance)

## 🚀 Installation

### 1. Installer les dépendances

Ouvrez un terminal dans le dossier du projet et exécutez :

```bash
pip install -r requirements.txt
```

### 2. Créer la base de données

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. (Optionnel) Créer un superutilisateur pour l'admin

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer un compte administrateur.

### 4. Lancer le serveur de développement

```bash
python manage.py runserver
```

Le serveur démarrera sur `http://localhost:8000`

## 📱 Utilisation

1. **Page d'atterrissage** (`http://localhost:8000/`)
   - Sélectionnez votre profil (débutant, trader confirmé, analyste)
   - Choisissez votre marché préféré (crypto, FIAT, commodities)

2. **Page d'accueil** (`http://localhost:8000/home/`)
   - Consultez le carrousel des paires populaires
   - Visualisez votre watchlist personnalisée
   - Ajoutez des paires à votre watchlist

3. **Page de recherche** (`http://localhost:8000/search/`)
   - Recherchez des paires par nom
   - Filtrez par type, prix, volume, variation
   - Changez le mode d'affichage (cartes/tableau)

4. **Page détaillée d'une paire** (`http://localhost:8000/pairs/BTCUSDT/`)
   - Prix en temps réel et variations
   - Graphiques interactifs (1h, 1j, 1s)
   - Carnet d'ordres et transactions récentes
   - Statistiques détaillées (ATH, ATL, volume)
   - Paires similaires

5. **Watchlist & Portfolio** (`http://localhost:8000/watchlist/`)
   - Gérez votre watchlist
   - Simulez votre portefeuille d'investissement
   - Suivez vos gains/pertes en temps réel

6. **Déconnexion** (`http://localhost:8000/accounts/logout/`)
   - Efface votre session et retourne à la landing page

## 🎨 Fonctionnalités

### ✅ Implémentées

- ✓ Sélection de profil utilisateur
- ✓ Gestion de session (sans authentification classique)
- ✓ Carrousel des paires populaires avec mini-graphiques
- ✓ Watchlist personnalisée persistante
- ✓ Portfolio de simulation avec calcul P&L
- ✓ Recherche avancée avec filtres multiples
- ✓ Pages détaillées avec graphiques Chart.js
- ✓ Carnet d'ordres et historique des transactions
- ✓ Design moderne et responsive (Bootstrap 5)
- ✓ Intégration complète API Binance
- ✓ Statistiques ATH/ATL sur 52 semaines
- ✓ Paires similaires et corrélées

### 🎁 Bonus possibles

- Alertes de prix par email/notification
- Widgets TradingView intégrés
- Connexion Metamask pour wallet crypto
- Visualisations géographiques blockchain
- Mode sombre/clair
- Multi-devises (EUR, USD, etc.)
- Export CSV/PDF des données
- Historique des performances du portfolio

## 🔧 Structure du Projet

```
Projet groupe Django monnaie/
├── crypto_monitor/          # Configuration principale Django
├── accounts/                # Gestion utilisateurs et sessions
├── api_services/            # Services API Binance
├── home/                    # Page d'accueil
├── landing/                 # Page d'atterrissage
├── pairs/                   # Pages détaillées des paires
├── search/                  # Recherche et filtres
├── watchlist/               # Watchlist et portfolio
├── templates/               # Templates HTML
├── static/                  # CSS et JavaScript
├── manage.py                # Script de gestion Django
├── requirements.txt         # Dépendances Python
└── README.md               # Documentation
```

## 🌐 API Binance

L'application utilise l'API publique Binance Spot :
- https://api.binance.com/api/v3/ticker/24hr
- https://api.binance.com/api/v3/exchangeInfo
- https://api.binance.com/api/v3/klines
- https://api.binance.com/api/v3/ticker/price
- https://api.binance.com/api/v3/depth
- https://api.binance.com/api/v3/trades

Documentation complète : https://binance-docs.github.io/apidocs/spot/en/

## 📝 Notes

- Aucune clé API n'est nécessaire (endpoints publics uniquement)
- Les données sont en temps réel via l'API Binance
- La base de données SQLite stocke les profils, watchlists et portfolios
- Les sessions sont gérées via Django sessions framework
- Le design est optimisé pour desktop et mobile

## 🐛 Résolution de problèmes

### Erreur "Module not found"
```bash
pip install -r requirements.txt
```

### Erreur de migration
```bash
python manage.py makemigrations
python manage.py migrate --run-syncdb
```

### Port 8000 déjà utilisé
```bash
python manage.py runserver 8080
```

### Erreurs d'API Binance
Vérifiez votre connexion Internet. L'API Binance peut avoir des limites de taux (rate limits).

## 🎓 Technologies Utilisées

- **Backend** : Django 4.2
- **Frontend** : Bootstrap 5, Chart.js
- **API** : Binance Spot REST API
- **Base de données** : SQLite3
- **Icons** : Bootstrap Icons

## 📧 Support

Pour toute question ou problème, consultez la documentation Django : https://docs.djangoproject.com/

---

**Bon trading ! 📈💰**

