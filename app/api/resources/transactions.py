import datetime
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Transaction, Category
from app.api.errors import api_error

import logging
from app.api.resources.auth import make_extra

logger = logging.getLogger(__name__)


class TransactionListAPI(Resource):
    @staticmethod
    def parse_date(date_str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"):
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError("Неверный формат даты")
    
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        
        logger.info("Запрос списка транзакций",
                   extra=make_extra(user_id=user_id))
        
        transactions = Transaction.query.filter(Transaction.user_id == user_id).all()
        transactions_list = []
        for t in transactions:
            transactions_list.append({
                "id": t.id,
                "amount": round(float(t.amount), 2),
                "type": t.type,
                "description": t.description,
                "date": t.date.strftime("%Y-%m-%d %H:%M:%S"),
                "category": t.category.name if t.category else None
            })
        
        logger.info("Список транзакций получен",
                   extra=make_extra(user_id=user_id,
                                   data={"count": len(transactions_list)}))
        
        return {"count": len(transactions_list), "transactions": transactions_list}
    
    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())
        
        logger.info("Запрос создания транзакции",
                   extra=make_extra(user_id=user_id))
        
        data = request.get_json()
        if not data:
            logger.warning("Отсутствует JSON тело при создании транзакции",
                          extra=make_extra(user_id=user_id))
            return api_error("Требуются JSON данные", 400)

        required = ['amount', 'type', 'description', 'category_id']
        missing = [field for field in required if field not in data]
        if missing:
            logger.warning("Отсутствуют обязательные поля для создания транзакции",
                          extra=make_extra(user_id=user_id,
                                          data={"missing_fields": missing}))
            return api_error("Отсутствуют поля", 400, f"{', '.join(missing)}")
        
        t_amount = data.get("amount", None)
        t_type = data.get("type", None)
        t_description = data.get("description", None)
        t_category_id = data.get("category_id", None)
        t_date = data.get("date", None)
        
        if t_amount < 0:
            logger.warning("Попытка создания транзакции с отрицательной суммой",
                          extra=make_extra(user_id=user_id,
                                          data={"amount": t_amount,
                                                "reason": "negative"}))
            return api_error("Поле amount не может быть отрицательным", 400, f"Получено: {t_amount}")
        
        if t_type not in ["income", "expense"]:
            logger.warning("Попытка создания транзакции с некорректным типом",
                          extra=make_extra(user_id=user_id,
                                          data={"type": t_type}))
            return api_error("Тип должен быть income или expense", 400, f"Получен {t_type}")
        
        category = Category.query.filter_by(id=t_category_id).first()
        if not category:
            logger.warning("Попытка создания транзакции с несуществующей категорией",
                          extra=make_extra(user_id=user_id,
                                          data={"category_id": t_category_id}))
            return api_error("Категория не найдена", 400)
        
        try:
            if not t_date:
                t_date = datetime.datetime.utcnow()
            else:
                t_date = TransactionListAPI.parse_date(t_date)
            
            transaction = Transaction(
                amount=t_amount,
                type=t_type,
                description=t_description,
                date=t_date,
                category_id=t_category_id,
                user_id=user_id
            )
            
        except Exception as e:
            if "date" in str(e).lower():
                logger.warning("Ошибка формата даты при создании транзакции",
                              extra=make_extra(user_id=user_id,
                                              data={"date_str": data.get("date")}))
            else:
                logger.error("Непредвиденная ошибка при создании объекта транзакции",
                            exc_info=True,
                            extra=make_extra(user_id=user_id))
            return api_error("Непредвиденная ошибка", 400, f"{str(e)}")
        
        try:
            db.session.add(transaction)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Ошибка базы данных при создании транзакции",
                        exc_info=True,
                        extra=make_extra(user_id=user_id,
                                        data={"amount": t_amount,
                                              "type": t_type}))
            return api_error("Ошибка базы данных", 500, f"{str(e)}")
        
        logger.info("Транзакция успешно создана",
                   extra=make_extra(user_id=user_id,
                                   data={"transaction_id": transaction.id,
                                         "amount": t_amount,
                                         "type": t_type}))
        
        return {
            "message": "Транзакция создана",
            "transaction": {
                "id": transaction.id,
                "amount": float(transaction.amount),
                "description": transaction.description,
                "date": transaction.date.strftime("%Y-%m-%d %H:%M:%S")
            }
        }, 201


class TransactionAPI(Resource):
    @jwt_required()
    def get(self, id):
        user_id = int(get_jwt_identity())
        
        logger.info("Запрос транзакции",
                   extra=make_extra(user_id=user_id,
                                   data={"transaction_id": id}))
        
        transaction = Transaction.query.filter_by(id=id).first()
        
        if not transaction:
            logger.warning("Транзакция не найдена",
                          extra=make_extra(user_id=user_id,
                                          data={"transaction_id": id}))
            return api_error("Транзакция не найдена", 404)
        
        if transaction.user_id != user_id:
            logger.warning("Попытка доступа к чужой транзакции",
                          extra=make_extra(user_id=user_id,
                                          data={"transaction_id": id,
                                                "owner_id": transaction.user_id}))
            return api_error("У вас недостаточно прав", 403)
        
        logger.info("Транзакция получена",
                   extra=make_extra(user_id=user_id,
                                   data={"transaction_id": id}))
        
        return {"transaction": {
                "id": transaction.id,
                "amount": round(float(transaction.amount), 2),
                "type": transaction.type,
                "description": transaction.description,
                "date": transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
                "category": transaction.category.name if transaction.category else None
            }}, 200
    
    @jwt_required() 
    def delete(self, id):
        user_id = int(get_jwt_identity())
        
        logger.info("Запрос удаления транзакции",
                   extra=make_extra(user_id=user_id,
                                   data={"transaction_id": id}))
        
        transaction = Transaction.query.filter_by(id=id).first()
        
        if not transaction:
            logger.warning("Транзакция для удаления не найдена",
                          extra=make_extra(user_id=user_id,
                                          data={"transaction_id": id}))
            return api_error("Транзакция не найдена", 404)
        
        if transaction.user_id != user_id:
            logger.warning("Попытка удаления чужой транзакции",
                          extra=make_extra(user_id=user_id,
                                          data={"transaction_id": id,
                                                "owner_id": transaction.user_id,
                                                "amount": float(transaction.amount),
                                                "type": transaction.type}))
            return api_error("У вас недостаточно прав", 403)
        
        # Сохраняем данные перед удалением для лога
        transaction_data = {
            "transaction_id": id,
            "amount": float(transaction.amount),
            "type": transaction.type
        }
        
        try:
            db.session.delete(transaction)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Ошибка при удалении транзакции",
                        exc_info=True,
                        extra=make_extra(user_id=user_id,
                                        data={"transaction_id": id}))
            return api_error("Ошибка при удалении", 500, f"{str(e)}")

        logger.info("Транзакция удалена",
                   extra=make_extra(user_id=user_id,
                                   data=transaction_data))
        
        return '', 204
    
    @jwt_required()
    def put(self, id):
        user_id = int(get_jwt_identity())
        
        logger.info("Запрос обновления транзакции",
                   extra=make_extra(user_id=user_id,
                                   data={"transaction_id": id}))
        
        transaction = Transaction.query.filter_by(id=id).first()
        if not transaction:
            logger.warning("Транзакция для обновления не найдена",
                          extra=make_extra(user_id=user_id,
                                          data={"transaction_id": id}))
            return api_error("Транзакция не найдена", 404)
        
        if transaction.user_id != user_id:
            logger.warning("Попытка обновления чужой транзакции",
                          extra=make_extra(user_id=user_id,
                                          data={"transaction_id": id,
                                                "owner_id": transaction.user_id}))
            return api_error("У вас недостаточно прав", 403)
        
        data = request.get_json()
        if not data:
            logger.warning("Нет данных для обновления транзакции",
                          extra=make_extra(user_id=user_id,
                                          data={"transaction_id": id}))
            return api_error("Нет данных для обновления", 400)
        
        if "amount" in data:
            if data["amount"] < 0:
                logger.warning("Попытка обновления с отрицательной суммой",
                              extra=make_extra(user_id=user_id,
                                              data={"transaction_id": id,
                                                    "amount": data["amount"]}))
                return api_error("Сумма не может быть отрицательной", 400, f"Получено {data['amount']}")
            transaction.amount = data["amount"]
        
        if "type" in data:
            if data["type"] not in ["income", "expense"]:
                logger.warning("Попытка обновления с некорректным типом",
                              extra=make_extra(user_id=user_id,
                                              data={"transaction_id": id,
                                                    "type": data["type"]}))
                return api_error("Тип должен быть income или expense", 400, f"Получен {data['type']}")
            transaction.type = data["type"]
        
        if "description" in data:
            transaction.description = data["description"]
        
        if "date" in data:
            try:
                date = TransactionListAPI.parse_date(data["date"])
                transaction.date = date
            except ValueError as e:
                logger.warning("Ошибка формата даты при обновлении транзакции",
                              extra=make_extra(user_id=user_id,
                                              data={"transaction_id": id,
                                                    "date_str": data["date"]}))
                return api_error("Непредвиденная ошибка", 400, f"{str(e)}")
        
        if "category_id" in data:
            category = Category.query.filter_by(id=data["category_id"]).first()
            if not category:
                logger.warning("Попытка обновления с несуществующей категорией",
                              extra=make_extra(user_id=user_id,
                                              data={"transaction_id": id,
                                                    "category_id": data["category_id"]}))
                return api_error("Категория не найдена", 400, f"Получено: {data['category_id']}")
            transaction.category_id = data["category_id"]
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Ошибка базы данных при обновлении транзакции",
                        exc_info=True,
                        extra=make_extra(user_id=user_id,
                                        data={"transaction_id": id,
                                              "updated_fields": list(data.keys())}))
            return api_error("Ошибка базы данных", 500, f"{str(e)}")
        
        logger.info("Транзакция обновлена",
                   extra=make_extra(user_id=user_id,
                                   data={"transaction_id": id,
                                         "updated_fields": list(data.keys())}))
        
        return {
            "message": "Обновлено",
            "transaction": {
                "id": transaction.id,
                "amount": round(float(transaction.amount), 2),
                "type": transaction.type,
                "description": transaction.description,
                "date": transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
                "category": transaction.category.name if transaction.category else None
            }
        }, 200