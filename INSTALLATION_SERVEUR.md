# 🚀 Guide Détaillé : Installation avec Script sur Serveur

## 📋 Étapes Complètes de Déploiement

### 1. Préparation Locale

#### A. Vérifier les fichiers nécessaires
```bash
# Dans votre dossier de projet local
ls -la
# Vérifiez que vous avez :
# - app.py
# - requirements.txt
# - templates/
# - static/
# - install_production.sh
# - create_admin.py
# - .env.example
```

#### B. Préparer l'archive du projet
```bash
# Créer une archive sans les fichiers inutiles
tar -czf mon-app.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='instance' \
    --exclude='.git' \
    --exclude='*.pyc' \
    .
```

### 2. Connexion au Serveur

#### A. Connexion SSH
```bash
# Remplacez par vos informations
ssh votre-utilisateur@votre-serveur.com

# Ou avec une clé SSH
ssh -i ~/.ssh/ma-cle.pem ubuntu@votre-serveur.com
```

#### B. Vérification des droits sudo
```bash
# Tester les droits administrateur
sudo whoami
# Doit afficher : root
```

### 3. Transfert des Fichiers

#### Option A: Avec SCP (depuis votre machine locale)
```bash
# Transférer l'archive
scp mon-app.tar.gz votre-utilisateur@votre-serveur.com:~/

# Ou transférer directement le dossier
scp -r /chemin/vers/votre-projet votre-utilisateur@votre-serveur.com:~/mon-app/
```

#### Option B: Avec rsync (plus efficace)
```bash
# Synchroniser le dossier (exclut automatiquement certains fichiers)
rsync -avz --exclude='venv' --exclude='__pycache__' \
    /chemin/vers/votre-projet/ \
    votre-utilisateur@votre-serveur.com:~/mon-app/
```

#### Option C: Avec Git (si votre projet est sur GitHub/GitLab)
```bash
# Sur le serveur
git clone https://github.com/votre-username/votre-repo.git mon-app
cd mon-app
```

### 4. Extraction et Préparation (si archive)

```bash
# Sur le serveur
cd ~
tar -xzf mon-app.tar.gz -C mon-app/
cd mon-app/
```

### 5. Exécution du Script d'Installation

#### A. Rendre le script exécutable
```bash
chmod +x install_production.sh
```

#### B. Vérifier le contenu du script (optionnel)
```bash
head -20 install_production.sh
```

#### C. Lancer l'installation
```bash
# Lancement interactif
./install_production.sh
```

### 6. Interaction avec le Script

Le script vous demandera plusieurs informations :

#### A. Nom de domaine
```
Entrez votre nom de domaine (ex: monsite.com) ou appuyez sur Entrée pour localhost:
```
**Réponses possibles :**
- `monsite.com` (votre vrai domaine)
- `Entrée` (pour localhost/IP)

#### B. Copie des fichiers
```
ATTENTION: Vous devez copier vos fichiers dans /var/www/client-manager
Exemple: scp -r /chemin/local/* user@serveur:/var/www/client-manager/
Appuyez sur Entrée une fois les fichiers copiés...
```

**Actions à faire :**
1. Ouvrir un **nouveau terminal** sur votre machine locale
2. Copier les fichiers :
```bash
# Depuis votre machine locale
scp -r ~/mon-projet/* votre-user@serveur:/var/www/client-manager/
```
3. Retourner au terminal du serveur et appuyer sur `Entrée`

#### C. Création de l'utilisateur admin
```
=== Création d'un utilisateur administrateur ===
Nom d'utilisateur: admin
Email: admin@monsite.com
Mot de passe: [tapez votre mot de passe]
```

#### D. Configuration HTTPS (optionnel)
```
Voulez-vous configurer HTTPS maintenant? (y/N):
```
- Tapez `y` si vous avez un domaine configuré
- Tapez `N` pour configurer plus tard

### 7. Vérification de l'Installation

#### A. Vérifier le statut de l'application
```bash
sudo supervisorctl status client-manager
# Doit afficher : RUNNING
```

#### B. Vérifier les logs
```bash
sudo tail -f /var/log/client-manager.log
```

#### C. Tester l'accès web
```bash
# Test local
curl http://localhost

# Test avec votre domaine
curl http://votre-domaine.com
```

### 8. Configuration Post-Installation

#### A. Modifier les paramètres email
```bash
sudo nano /var/www/client-manager/.env
```

**Modifier ces lignes :**
```bash
EMAIL_EXPEDITEUR=votre-vrai-email@gmail.com
MOT_DE_PASSE_EMAIL=votre-mot-de-passe-app-gmail
```

#### B. Redémarrer l'application
```bash
sudo supervisorctl restart client-manager
```

#### C. Configurer le DNS (si domaine)
Dans votre panneau de contrôle DNS :
- Type : `A`
- Nom : `@` (ou votre domaine)
- Valeur : `IP-de-votre-serveur`
- TTL : `300`

## 🔧 Commandes Utiles Post-Installation

### Gestion de l'Application
```bash
# Voir le statut
sudo supervisorctl status client-manager

# Redémarrer
sudo supervisorctl restart client-manager

# Arrêter
sudo supervisorctl stop client-manager

# Démarrer
sudo supervisorctl start client-manager
```

### Logs et Débogage
```bash
# Logs de l'application
sudo tail -f /var/log/client-manager.log

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Tester la configuration Nginx
sudo nginx -t
```

### Base de Données
```bash
# Accéder à la base SQLite
sqlite3 /var/www/client-manager/instance/clients.db

# Sauvegarder manuellement
sqlite3 /var/www/client-manager/instance/clients.db '.backup backup.db'

# Voir les sauvegardes automatiques
ls -la /var/backups/clients_*
```

## 🚨 Résolution de Problèmes

### Erreur : "Permission denied"
```bash
sudo chown -R www-data:www-data /var/www/client-manager
sudo chmod +x /var/www/client-manager/install_production.sh
```

### Erreur : "Port 80 already in use"
```bash
# Voir ce qui utilise le port 80
sudo netstat -tulpn | grep :80

# Arrêter Apache si installé
sudo systemctl stop apache2
sudo systemctl disable apache2
```

### Erreur : "Database locked"
```bash
sudo supervisorctl stop client-manager
sudo chown www-data:www-data /var/www/client-manager/instance/clients.db
sudo supervisorctl start client-manager
```

### Application ne répond pas
```bash
# Vérifier les processus
ps aux | grep python

# Redémarrer complètement
sudo supervisorctl restart client-manager
sudo systemctl reload nginx
```

## ✅ Checklist Finale

- [ ] Application accessible via navigateur
- [ ] Login administrateur fonctionne
- [ ] Ajout de client fonctionne
- [ ] Envoi d'email de test réussi
- [ ] HTTPS configuré (si domaine)
- [ ] Sauvegardes automatiques actives
- [ ] Firewall configuré

## 📞 Support

En cas de problème, vérifiez dans l'ordre :
1. **Logs** : `/var/log/client-manager.log`
2. **Statut** : `sudo supervisorctl status`
3. **Permissions** : `ls -la /var/www/client-manager/`
4. **Configuration** : `sudo nginx -t`

**Votre application est maintenant en production ! 🎉**
