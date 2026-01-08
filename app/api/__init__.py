from flask import Blueprint
from flask_restful import Api

from app.api.resources.transactions import TransactionListAPI, TransactionAPI
from app.api.resources.categories import CategoryListAPI
from app.api.resources.auth import LoginAPI, RefreshTokenAPI, LogoutAPI
from app.api.resources.profile import ProfileAPI, ChangePasswordAPI

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(TransactionListAPI, "/transactions")
api.add_resource(TransactionAPI, "/transactions/<int:id>")
api.add_resource(CategoryListAPI, "/categories")
api.add_resource(LoginAPI, "/auth/login")
api.add_resource(RefreshTokenAPI, "/auth/refresh")
api.add_resource(LogoutAPI, "/auth/logout")
api.add_resource(ProfileAPI, "/profile")
api.add_resource(ChangePasswordAPI, "/profile/password")
