import logging
from datetime import timedelta

from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from app.models import User
from app.api.errors import api_error

logger = logging.getLogger(__name__)


def make_extra(user_id=None, data=None):
    """Хелпер для создания контекста логов."""
    extra = {
        "endpoint": request.path,
        "method": request.method,
        "ip": request.remote_addr,
        "user_agent": (
            request.user_agent.string[:100] if request.user_agent else None
        ),
    }
    # Разрешаем передавать явно "[REDACTED]" для скрытия данных
    if data is not None:
        extra["entered_data"] = data
    if user_id is not None:
        extra["user_id"] = user_id
    return extra


class LoginAPI(Resource):
    def post(self):
        logger.info("Запрос аутентификации", extra=make_extra())
        data = request.get_json()
        if not data:
            logger.warning("Отсутствует JSON тело", extra=make_extra())
            return api_error("Требуется JSON тело", 400)
        if "username" not in data or "password" not in data:
            attempted_username = data.get("username")
            logger.warning(
                "Отсутствуют обязательные поля",
                extra=make_extra(
                    data={"attempted_username": attempted_username}
                ),
            )
            return api_error("Отсутствуют данные", 400)
        user = User.query.filter_by(username=data["username"]).first()
        if not user or not user.check_password(data["password"]):
            logger.warning(
                "Неудачная попытка входа",
                extra=make_extra(
                    data={"attempted_username": data["username"]}
                ),
            )
            return api_error("Неверные данные", 401)
        access_token = create_access_token(
            identity=str(user.id), expires_delta=timedelta(minutes=15)
        )
        refresh_token = create_refresh_token(
            identity=str(user.id), expires_delta=timedelta(days=7)
        )
        logger.info(
            "Успешная аутентификация",
            extra=make_extra(
                user_id=user.id, data={"username": user.username}
            ),
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user.id,
            "username": user.username,
        }, 200


class RefreshTokenAPI(Resource):
    @jwt_required(refresh=True)
    def post(self):
        user_id = get_jwt_identity()
        logger.info(
            "Запрос обновления токена", extra=make_extra(user_id=user_id)
        )
        new_access_token = create_access_token(
            identity=str(user_id), expires_delta=timedelta(minutes=15)
        )
        logger.info(
            "Токен успешно обновлен", extra=make_extra(user_id=user_id)
        )
        return {"access_token": new_access_token}, 200


class LogoutAPI(Resource):
    @jwt_required(refresh=True)
    def post(self):
        user_id = get_jwt_identity()
        logger.info(
            "Запрос выхода из системы", extra=make_extra(user_id=user_id)
        )
        logger.info("Выход выполнен", extra=make_extra(user_id=user_id))
        return {
            "message": "Успешный выход. Удалите токены на клиенте.",
            "note": "Access токен истечет через 15 мин, refresh через 7 дней",
        }, 200
