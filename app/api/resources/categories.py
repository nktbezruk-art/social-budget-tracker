import logging

from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import Category
from app.api.resources.auth import make_extra

logger = logging.getLogger(__name__)


class CategoryListAPI(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        logger.info(
            "Запрос списка категорий",
            extra=make_extra(user_id=user_id)
        )
        categories = Category.query.all()
        categories_list = [
            {"id": category.id, "name": category.name}
            for category in categories
        ]
        logger.info(
            "Список категорий получен",
            extra=make_extra(
                user_id=user_id,
                data={"count": len(categories)}
            )
        )
        return {
            "count": len(categories),
            "categories": categories_list,
        }
