# Guide de Déploiement en Production

## 📋 Prérequis

- Serveur Linux (Ubuntu/Debian recommandé)
- Python 3.8+ installé
- Accès SSH au serveur
- Nom de domaine (optionnel pour HTTPS)

## 🔧 Installation SQLite en Production

### 1. Connexion au serveur
```bash
ssh votre-utilisateur@votre-serveur.com
```

### 2. Mise à jour du système
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Installation des dépendances système
```bash
# Python et pip
sudo apt install python3 python3-pip python3-venv -y

# SQLite (généralement déjà installé)
sudo apt install sqlite3 libsqlite3-dev -y

# Nginx (serveur web)
sudo apt install nginx -y

# Supervisor (gestion des processus)
sudo apt install supervisor -y

# Outils SSL
sudo apt install certbot python3-certbot-nginx -y
```

### 4. Vérification de SQLite
```bash
sqlite3 --version
# Devrait afficher la version (ex: 3.31.1)
```

## 📁 Déploiement de l'Application

### 1. Cloner le projet
```bash
cd /var/www/
sudo mkdir votre-app
sudo chown $USER:$USER votre-app
cd votre-app

# Copier vos fichiers via SCP ou Git
scp -r /chemin/local/vers/projet/* votre-utilisateur@serveur:/var/www/votre-app/
```

### 2. Configuration de l'environnement Python
```bash
cd /var/www/votre-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration des variables d'environnement
```bash
# Copier et modifier le fichier .env
cp .env.example .env
nano .env
```

**Modifier le fichier .env pour la production :**
```bash
# Configuration pour l'envoi d'emails
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_EXPEDITEUR=votre-email@gmail.com
MOT_DE_PASSE_EMAIL=votre-mot-de-passe-app

# Configuration de sécurité (IMPORTANT: Changer cette clé!)
SECRET_KEY=une-cle-super-secrete-longue-et-unique-pour-production

# Configuration base de données SQLite
DATABASE_URL=sqlite:////var/www/votre-app/instance/clients.db

# Configuration HTTPS
SSL_DISABLE=False
```

### 4. Initialisation de la base de données
```bash
# Créer le dossier instance
mkdir -p instance

# Initialiser la base de données
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Créer un utilisateur administrateur
python3 create_admin.py
```

### 5. Test de l'application
```bash
# Test rapide
python3 app.py
# Ctrl+C pour arrêter
```

## 🌐 Configuration Nginx

### 1. Créer la configuration Nginx
```bash
sudo nano /etc/nginx/sites-available/votre-app
```

**Contenu du fichier :**
```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/votre-app/static;
        expires 30d;
    }
}
```

### 2. Activer la configuration
```bash
sudo ln -s /etc/nginx/sites-available/votre-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Configuration HTTPS avec Let's Encrypt

### 1. Obtenir le certificat SSL
```bash
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

### 2. Renouvellement automatique
```bash
sudo crontab -e
# Ajouter cette ligne :
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔄 Configuration Supervisor (Démarrage automatique)

### 1. Créer la configuration Supervisor
```bash
sudo nano /etc/supervisor/conf.d/votre-app.conf
```

**Contenu du fichier :**
```ini
[program:votre-app]
command=/var/www/votre-app/venv/bin/python app.py
directory=/var/www/votre-app
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/votre-app.log
environment=FLASK_ENV=production
```

### 2. Démarrer l'application
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start votre-app
sudo supervisorctl status
```

## 🛡️ Sécurisation

### 1. Permissions des fichiers
```bash
sudo chown -R www-data:www-data /var/www/votre-app
sudo chmod -R 755 /var/www/votre-app
sudo chmod 600 /var/www/votre-app/.env
sudo chmod 664 /var/www/votre-app/instance/clients.db
```

### 2. Firewall
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
```

## 📊 Maintenance

### 1. Logs de l'application
```bash
sudo tail -f /var/log/votre-app.log
```

### 2. Logs Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. Redémarrer l'application
```bash
sudo supervisorctl restart votre-app
```

### 4. Sauvegarde de la base de données
```bash
# Script de sauvegarde quotidienne
echo "#!/bin/bash
sqlite3 /var/www/votre-app/instance/clients.db '.backup /var/backups/clients_\$(date +%Y%m%d).db'
find /var/backups -name 'clients_*.db' -mtime +30 -delete" | sudo tee /usr/local/bin/backup-db.sh

sudo chmod +x /usr/local/bin/backup-db.sh

# Ajouter au crontab
sudo crontab -e
# Ajouter : 0 2 * * * /usr/local/bin/backup-db.sh
```

## ✅ Vérification finale

1. **Test de l'application** : `curl http://votre-domaine.com`
2. **Test HTTPS** : `curl https://votre-domaine.com`
3. **Test de redirection** : Vérifier que HTTP redirige vers HTTPS
4. **Test des emails** : Envoyer un email de test depuis l'interface
5. **Test des rappels automatiques** : Vérifier les logs

## 🚨 Dépannage

### Application ne démarre pas
```bash
sudo supervisorctl status votre-app
sudo tail -f /var/log/votre-app.log
```

### Erreur de base de données
```bash
ls -la /var/www/votre-app/instance/
sudo chown www-data:www-data /var/www/votre-app/instance/clients.db
```

### Problème SSL
```bash
sudo certbot certificates
sudo nginx -t
sudo systemctl reload nginx
```

---

**🎉 Votre application est maintenant en production avec SQLite !**

Pour toute question ou problème, consultez les logs et vérifiez les permissions des fichiers.
