import logging
import re

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User
from app.api.errors import api_error
from app.db import db
from app.api.resources.auth import make_extra

logger = logging.getLogger(__name__)


def validation_logger_warning(user_id, field_name, data):
    """Логирование валидационных ошибок."""
    # Не логируем пароли
    log_data = "[REDACTED]" if field_name == "password" else data
    return logger.warning(
        "Валидационная ошибка при изменении данных профиля",
        extra=make_extra(user_id=user_id, data=log_data)
    )


class ProfileAPI(Resource):
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        logger.info(
            "Запрос профиля пользователя",
            extra=make_extra(user_id=user_id)
        )
        user = User.query.get(user_id)
        if not user:
            logger.warning(
                "Пользователь не найден при запросе профиля",
                extra=make_extra(user_id=user_id)
            )
            return api_error(f"Пользователь с id {user_id} не найден", 404)
        logger.info(
            "Профиль успешно получен",
            extra=make_extra(user_id=user_id)
        )
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        }, 200

    @jwt_required()
    def put(self):
        data = request.get_json()
        user_id = int(get_jwt_identity())
        logger.info(
            "Запрос на обновление профиля",
            extra=make_extra(user_id=user_id)
        )
        user = User.query.get(user_id)
        if not user:
            logger.warning(
                "Пользователь не найден при попытке обновления профиля",
                extra=make_extra(user_id=user_id)
            )
            return api_error("Пользователь не найден", 404)
        if "username" in data:
            username = data["username"]
            if len(username) < 3:
                validation_logger_warning(user_id, "username", username)
                return api_error(
                    "Имя пользователя должно быть не короче 3 символов", 400
                )
            if len(username) > 20:
                validation_logger_warning(user_id, "username", username)
                return api_error(
                    "Имя пользователя должно быть не длиннее 20 символов", 400
                )
            if not username.isalnum():
                validation_logger_warning(user_id, "username", username)
                return api_error(
                    "Имя должно содержать только буквы и цифры", 400
                )
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user_id:
                logger.warning(
                    "Попытка присвоения существующего имени",
                    extra=make_extra(user_id=user_id)
                )
                return api_error("Данное имя уже занято", 409)
            logger.info(
                "Успешное изменение имени пользователя",
                extra=make_extra(user_id=user_id, data=username)
            )
            user.username = username

        if "email" in data:
            email = data["email"]
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                validation_logger_warning(user_id, "email", email)
                return api_error("Неверный формат email", 400)
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user_id:
                logger.warning(
                    "Попытка присвоения существующей почты",
                    extra=make_extra(user_id=user_id)
                )
                return api_error("Данная почта уже занята", 409)
            logger.info(
                "Успешное изменение почты пользователя",
                extra=make_extra(user_id=user_id, data=email)
            )
            user.email = email

        try:
            db.session.commit()
        except Exception as e:
            logger.error(
                "Ошибка при попытке сохранения изменений",
                exc_info=True,
                extra=make_extra(user_id=user_id)
            )
            return api_error("Непредвиденная ошибка", 400, f"{str(e)}")
        else:
            logger.info(
                "Профиль успешно обновлен",
                extra=make_extra(user_id=user_id)
            )
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            }, 200


class ChangePasswordAPI(Resource):
    @jwt_required()
    def put(self):
        user_id = int(get_jwt_identity())
        logger.info(
            "Запрос на смену пароля",
            extra=make_extra(user_id=user_id)
        )
        user = User.query.get(user_id)
        if not user:
            logger.warning(
                "Пользователь не найден при попытке смены пароля",
                extra=make_extra(user_id=user_id)
            )
            return api_error("Пользователь не найден", 404)
        data = request.get_json()

        if "current_password" not in data or "new_password" not in data:
            logger.warning(
                "Отсутствуют обязательные поля для смены пароля",
                extra=make_extra(user_id=user_id)
            )
            return api_error("Отсутствуют данные", 401)

        current_password = data["current_password"]
        new_password = data["new_password"]

        if not user.check_password(current_password):
            logger.warning(
                "Неверный текущий пароль",
                extra=make_extra(user_id=user_id)
            )
            return api_error("Неверный пароль", 401)
        if len(new_password) < 6:
            validation_logger_warning(user_id, "password", new_password)
            return api_error(
                "Новый пароль должен содержать минимум 6 символов", 400
            )

        if current_password == new_password:
            validation_logger_warning(user_id, "password", new_password)
            return api_error("Новый пароль не должен совпадать с текущим", 400)

        if not any(char.isdigit() for char in new_password):
            validation_logger_warning(user_id, "password", new_password)
            return api_error("Пароль должен содержать хотя бы одну цифру", 400)

        if new_password.lower() in [user.username.lower(), user.email.lower()]:
            validation_logger_warning(user_id, "password", new_password)
            return api_error(
                "Пароль не должен содержать имя пользователя или email", 400
            )
        logger.info(
            "Пароль успешно изменен",
            extra=make_extra(user_id=user_id)
        )
        user.set_password(new_password)

        try:
            db.session.commit()
        except Exception as e:
            logger.error(
                "Ошибка базы данных при смене пароля",
                exc_info=True,
                extra=make_extra(user_id=user_id)
            )
            return api_error("Непредвиденная ошибка", 400, f"{str(e)}")
        else:
            logger.info(
                "Пароль успешно сохранен",
                extra=make_extra(user_id=user_id)
            )
            return {
                "message": "Пароль успешно изменен"
            }, 200
