#!/usr/bin/env python3
"""
Script de configuration pour la production avec HTTPS
Usage: python production_setup.py
"""

import os
import ssl
from app import app

def setup_https():
    """Configure HTTPS pour la production"""
    
    # Configuration SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Chemins vers les certificats (à adapter selon votre configuration)
    cert_file = 'cert.pem'  # Certificat SSL
    key_file = 'key.pem'    # Clé privée
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        context.load_cert_chain(cert_file, key_file)
        print("✅ Certificats SSL chargés")
        return context
    else:
        print("⚠️  Certificats SSL non trouvés")
        print("Pour générer des certificats auto-signés (développement uniquement):")
        print("openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes")
        return None

def run_production():
    """Lance l'application en mode production"""
    
    print("=== Configuration Production ===")
    
    # Vérifier les variables d'environnement critiques
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == 'votre-cle-secrete-super-longue-et-complexe-changez-moi-en-production':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        print("Veuillez configurer le fichier .env avant de lancer en production")
        return
    
    # Configuration HTTPS
    ssl_context = setup_https()
    
    # Lancer l'application
    if ssl_context:
        print("🚀 Lancement en HTTPS sur le port 443")
        app.run(host='0.0.0.0', port=443, ssl_context=ssl_context, debug=False)
    else:
        print("🚀 Lancement en HTTP sur le port 80 (non sécurisé)")
        app.run(host='0.0.0.0', port=80, debug=False)

if __name__ == '__main__':
    run_production()
