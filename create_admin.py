#!/usr/bin/env python3
"""
Script pour créer un utilisateur administrateur
Usage: python create_admin.py
"""

from app import app, db, User
import getpass

def create_admin_user():
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        print("=== Création d'un utilisateur administrateur ===")
        
        username = input("Nom d'utilisateur: ")
        email = input("Email: ")
        password = getpass.getpass("Mot de passe: ")
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            print(f"Erreur: L'utilisateur '{username}' existe déjà!")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"Erreur: L'email '{email}' est déjà utilisé!")
            return
        
        # Créer l'utilisateur
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ Utilisateur administrateur '{username}' créé avec succès!")
        print("Vous pouvez maintenant vous connecter à l'application.")

if __name__ == '__main__':
    create_admin_user()
