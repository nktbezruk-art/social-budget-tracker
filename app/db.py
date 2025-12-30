from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
jwt = JWTManager()
login_manager.login_view = "auth.login" # type: ignore
login_manager.login_message = "Для доступа необходимо войти в аккаунт!" # type: ignore

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))