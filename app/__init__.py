from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from config import config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from .main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

        from .clients import clients as clients_blueprint
        app.register_blueprint(clients_blueprint)

        from .emails import emails as emails_blueprint
        app.register_blueprint(emails_blueprint)

        from .email import envoyer_rappels_automatiques_func

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=envoyer_rappels_automatiques_func,
            trigger="interval",
            days=7,  # Vérifie chaque semaine
            id='rappels_automatiques'
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

    return app
