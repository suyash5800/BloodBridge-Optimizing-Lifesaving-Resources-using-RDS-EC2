from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # login page redirect

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Blueprints import
    from app.routes import main, auth, donor, hospital, blood_bank, admin

    # Blueprints register
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(donor.bp)
    app.register_blueprint(hospital.bp)
    app.register_blueprint(blood_bank.bp)
    app.register_blueprint(admin.bp)

    # Table create
    with app.app_context():
        from app import models
        db.create_all()

    return app


