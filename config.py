import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'votre_cle_secrete_par_defaut')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration email
    SMTP_SERVER = 'smtp.example.com'
    SMTP_PORT = 587
    EMAIL_EXPEDITEUR = os.environ.get('EMAIL_EXPEDITEUR')
    MOT_DE_PASSE_EMAIL = os.environ.get('MOT_DE_PASSE_EMAIL')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
