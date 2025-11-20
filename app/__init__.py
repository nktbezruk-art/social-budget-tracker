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
    
    return app