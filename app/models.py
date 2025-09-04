from .extensions import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telephone = db.Column(db.String(20))
    date_derniere_visite = db.Column(db.Date)
    date_ajout = db.Column(db.Date, default=lambda: datetime.now().date())
    date_expiration = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='envoyé')
    client = db.relationship('Client', backref=db.backref('emails', lazy=True))

    def __repr__(self):
        return f'<Client {self.nom}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
