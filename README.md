# Application de Rappels Clients

Une application web Flask pour gérer les clients et envoyer des rappels automatiques par email.

## Fonctionnalités

- **Gestion des clients** : Ajouter, modifier, supprimer des clients
- **Envoi d'emails** : Envoyer des emails personnalisés aux clients
- **Rappels automatiques** : Système automatique de rappels d'expiration d'abonnement
- **Interface moderne** : Interface utilisateur responsive avec Bootstrap

## Installation

1. **Cloner le projet** (si applicable)
```bash
git clone [url-du-repo]
cd windsurf-project
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou
venv\Scripts\activate  # Sur Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration des emails**
```bash
cp .env.example .env
```
Modifiez le fichier `.env` avec vos paramètres email.

## Configuration Email

Pour Gmail :
1. Activez la validation en deux étapes
2. Générez un mot de passe d'application
3. Utilisez ce mot de passe dans le fichier `.env`

## Utilisation

1. **Démarrer l'application**
```bash
python app.py
```

2. **Accéder à l'application**
Ouvrez votre navigateur à l'adresse : `http://localhost:5000`

## Structure du Projet

```
windsurf-project/
├── app.py                 # Application Flask principale
├── requirements.txt       # Dépendances Python
├── .env.example          # Exemple de configuration
├── clients.db            # Base de données SQLite (créée automatiquement)
├── templates/            # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── ajouter_client.html
│   ├── modifier_client.html
│   ├── envoyer_email.html
│   └── rappels.html
└── static/               # Fichiers statiques
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Fonctionnalités Principales

### Gestion des Clients
- Ajouter de nouveaux clients avec leurs informations
- Modifier les informations existantes
- Suivre la date de dernière visite
- Gérer le statut (actif/inactif)

### Envoi d'Emails
- Interface pour composer des emails personnalisés
- Modèles de messages prédéfinis
- Envoi immédiat aux clients sélectionnés

### Rappels Automatiques
- Système automatique qui s'exécute quotidiennement
- Détecte les clients dont l'abonnement expire dans 2 jours
- Envoie des rappels d'expiration personnalisés automatiquement

## Fonctionnalités Avancées

### Dashboard
- Graphiques et statistiques des clients
- Vue d'ensemble des métriques importantes
- Cartes de statistiques interactives

### Export
- Export Excel/PDF de la liste des clients
- Téléchargement direct depuis l'interface
- Données formatées et prêtes à l'impression

### Recherche
- Barre de recherche et filtres avancés
- Recherche par nom, email ou téléphone
- Filtrage par statut (actif/inactif)

### Templates
- Modèles d'emails personnalisables
- Réutilisation rapide de messages types
- Variables dynamiques pour personnalisation

### Historique
- Log complet des emails envoyés
- Pagination et recherche dans l'historique
- Statut de livraison des emails

## Sécurité

- Authentification obligatoire avec Flask-Login
- Mots de passe hashés avec bcrypt
- Sessions sécurisées
- Utilisez des mots de passe d'application pour Gmail
- Ne commitez jamais le fichier `.env` dans votre repository
- Gardez vos informations de connexion email sécurisées

## Support

Pour toute question ou problème, consultez la documentation Flask ou contactez le développeur.
# recrouvrement-v2
