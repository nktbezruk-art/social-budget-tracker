import os
from flask import Flask
from config import ProductionConfig, DevelopmentConfig, TestConfig
from app.db import db, migrate, login_manager, csrf

def create_app():
    app = Flask(__name__)
    
    config_name = os.environ.get("FLASK_ENV", "development")
        
    if config_name == "development":
        app.config.from_object(DevelopmentConfig)
    elif config_name == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(TestConfig)
        
    if not os.environ.get("SECRET_KEY", ""):
        raise ValueError("SECRET_KEY must be set in .env file")
    
    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    from app import models
    
    from app.auth import auth_bp
    from app.reports import reports_bp
    from app.social import social_bp
    from app.transactions import transactions_bp
    from app.main import main_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(transactions_bp)

    from app import commands
    commands.register_commands(app)
    
    return app
