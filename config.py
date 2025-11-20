import os
from dotenv import load_dotenv

load_dotenv()

class Config():
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    DEBUG = os.environ.get("DEBUG") == "True"
    FLASK_ENV = os.environ.get("FLASK_ENV")
    
class DevelopmentConfig(Config):
    pass
    
    
class ProductionConfig(Config):
    pass

class TestConfig(Config):
    TESTING = True