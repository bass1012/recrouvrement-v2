#!/bin/bash

# Script d'installation automatique pour la production avec SQLite
# Usage: chmod +x install_production.sh && ./install_production.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Installation de l'application Flask en production avec SQLite"
echo "=============================================================="

# Variables de configuration
APP_NAME="client-manager"
APP_DIR="/var/www/$APP_NAME"
DOMAIN=""

# Demander le nom de domaine
read -p "Entrez votre nom de domaine (ex: monsite.com) ou appuyez sur Entrée pour localhost: " DOMAIN
if [ -z "$DOMAIN" ]; then
    DOMAIN="localhost"
fi

echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

echo "🔧 Installation des dépendances système..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    libsqlite3-dev \
    nginx \
    supervisor \
    certbot \
    python3-certbot-nginx \
    ufw

echo "📁 Création du répertoire d'application..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

echo "🐍 Configuration de l'environnement Python..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Copier les fichiers (à adapter selon votre méthode de déploiement)
echo "📋 Copie des fichiers d'application..."
echo "ATTENTION: Vous devez copier vos fichiers dans $APP_DIR"
echo "Exemple: scp -r /chemin/local/* user@serveur:$APP_DIR/"
read -p "Appuyez sur Entrée une fois les fichiers copiés..."

# Installation des dépendances Python
if [ -f "requirements.txt" ]; then
    echo "📦 Installation des dépendances Python..."
    pip install -r requirements.txt
else
    echo "❌ Fichier requirements.txt non trouvé!"
    exit 1
fi

echo "🔐 Configuration des variables d'environnement..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo "Fichier .env.example non trouvé, création manuelle nécessaire"
fi

# Générer une clé secrète aléatoire
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Modifier le fichier .env
cat > .env << EOF
# Configuration pour l'envoi d'emails
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_EXPEDITEUR=votre-email@gmail.com
MOT_DE_PASSE_EMAIL=votre-mot-de-passe-app

# Configuration de sécurité
SECRET_KEY=$SECRET_KEY

# Configuration base de données SQLite
DATABASE_URL=sqlite:///$APP_DIR/instance/clients.db

# Configuration HTTPS
SSL_DISABLE=False
EOF

echo "📊 Initialisation de la base de données..."
mkdir -p instance
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

echo "👤 Création d'un utilisateur administrateur..."
python3 create_admin.py

echo "🌐 Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $APP_DIR/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Activer le site
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

echo "🔄 Configuration de Supervisor..."
sudo tee /etc/supervisor/conf.d/$APP_NAME.conf > /dev/null << EOF
[program:$APP_NAME]
command=$APP_DIR/venv/bin/python app.py
directory=$APP_DIR
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/$APP_NAME.log
environment=FLASK_ENV=production
EOF

echo "🛡️ Configuration des permissions..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR
sudo chmod 600 $APP_DIR/.env
sudo chmod 664 $APP_DIR/instance/clients.db

echo "🔥 Configuration du firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

echo "🚀 Démarrage de l'application..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start $APP_NAME

# Configuration HTTPS si domaine fourni
if [ "$DOMAIN" != "localhost" ]; then
    echo "🔒 Configuration HTTPS avec Let's Encrypt..."
    read -p "Voulez-vous configurer HTTPS maintenant? (y/N): " setup_https
    if [[ $setup_https =~ ^[Yy]$ ]]; then
        sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN
        
        # Renouvellement automatique
        (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
    fi
fi

echo "📋 Configuration de la sauvegarde automatique..."
sudo tee /usr/local/bin/backup-$APP_NAME.sh > /dev/null << EOF
#!/bin/bash
BACKUP_DIR="/var/backups"
mkdir -p \$BACKUP_DIR
sqlite3 $APP_DIR/instance/clients.db ".backup \$BACKUP_DIR/clients_\$(date +%Y%m%d_%H%M%S).db"
find \$BACKUP_DIR -name "clients_*.db" -mtime +30 -delete
EOF

sudo chmod +x /usr/local/bin/backup-$APP_NAME.sh
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-$APP_NAME.sh") | sudo crontab -

echo ""
echo "✅ Installation terminée avec succès!"
echo "============================================"
echo "🌐 URL de l'application: http://$DOMAIN"
if [ "$DOMAIN" != "localhost" ]; then
    echo "🔒 HTTPS: https://$DOMAIN (si configuré)"
fi
echo "📁 Répertoire: $APP_DIR"
echo "📊 Logs: sudo tail -f /var/log/$APP_NAME.log"
echo "🔄 Redémarrer: sudo supervisorctl restart $APP_NAME"
echo "📋 Status: sudo supervisorctl status $APP_NAME"
echo ""
echo "⚠️  N'oubliez pas de:"
echo "   1. Modifier les paramètres email dans $APP_DIR/.env"
echo "   2. Tester l'envoi d'emails depuis l'interface"
echo "   3. Configurer votre DNS pour pointer vers ce serveur"
echo ""
echo "🎉 Votre application de gestion de clients est maintenant en ligne!"
