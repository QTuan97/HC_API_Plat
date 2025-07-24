import os
from flask import Flask
from flask_jwt_extended import JWTManager
from .db import db
from .models import User, MockRule, LoggedRequest
from .routes_ui import ui_bp
from .routes_api import api_bp

def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )
    # Core config
    app.config.update({
        "SQLALCHEMY_DATABASE_URI": os.environ["DATABASE_URL"],
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY":             os.environ.get("SECRET_KEY", "dev-secret-key"),
        "JWT_SECRET_KEY":         os.environ.get("JWT_SECRET_KEY"),
    })

    # Initialize extensions
    db.init_app(app)
    JWTManager(app)

    # Register your UI & API blueprints
    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)

    # **Create tables once models are loaded**
    with app.app_context():
        db.create_all()

    return app
