import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in .env file")
    
    DEBUG = os.environ.get("DEBUG", "False") == "True"
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    
    BASE_DIR = Path(__file__).parent.parent
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR}/instance/database.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_PROTECTION = "strong"

class DevelopmentConfig(Config):
    TEMPLATES_AUTO_RELOAD = True
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False