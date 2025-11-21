import os
from flask import Flask
from config import ProductionConfig, DevelopmentConfig, TestConfig

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
    
    
    from app.auth import auth_bp
    from app.reports import reports_bp
    from app.social import social_bp
    from app.transactions import transactions_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(transactions_bp)
    
    @app.route("/test")
    def test():
        return "FLASK WORKS!"

    return app
