import logging
from datetime import datetime, time
from decimal import Decimal
from flask import url_for, redirect, render_template, session, flash, request
from flask_login import current_user, login_required
from . import transactions_bp
from app import db
from app.models import Transaction, User
from app.forms import TransactionForm, DeleteConfirmForm, FilterForm

logger = logging.getLogger(__name__)

def apply_transaction_filters(query, form):
    from datetime import date, timedelta
    from app.models import Category, Transaction
    
    period = form.period.data
    category_id = form.category_id.data
    transaction_type = form.transaction_type.data
    
    description_parts = []
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    if period == "today":
        query = query.filter(Transaction.date >= today,
                            Transaction.date < tomorrow)
        description_parts.append("сегодня")
        
    elif period == "this_week":
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        query = query.filter(Transaction.date >= monday,
                            Transaction.date < tomorrow)
        description_parts.append("за эту неделю")
        
    elif period == "this_month":
        first_of_the_month = date(today.year, today.month, 1)
        query = query.filter(Transaction.date >= first_of_the_month,
                            Transaction.date < tomorrow)
        description_parts.append("за этот месяц")
    
    elif period == "last_3_months":
        three_month_ago = today - timedelta(days=90)
        query = query.filter(Transaction.date >= three_month_ago,
                            Transaction.date < tomorrow)
        description_parts.append("за последние 3 мeсяца")
        
    elif period == "this_year":
        first_of_the_year = date(today.year, 1, 1)
        query = query.filter(Transaction.date >= first_of_the_year,
                            Transaction.date < tomorrow)
        description_parts.append("за этот год")
    
    elif period == "all_time":
        description_parts.append("за все время")
    
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
        category = Category.query.get(category_id)
        if category:
            description_parts.append(f"{category.name}")
    
    if transaction_type == "all":
        description_parts.append("Все")
        
    elif transaction_type == "income":
        query = query.filter(Transaction.type == "income")
        description_parts.append("Доходы")
    
    elif transaction_type == "expense":
        query = query.filter(Transaction.type == "expense")
        description_parts.append("Расходы")
        

    if not description_parts:
        description = "без фильтров"
    else:
        description = " • ".join(description_parts)
    
    return query, description
        
    
@transactions_bp.route("/")
@login_required
def transaction_main():
    logger.info("Показ транзакций пользователя %s", current_user.id)
    form = FilterForm(request.args)
    # Начинаем с запроса, отфильтрованного по текущему пользователю
    query = Transaction.query.filter_by(user_id=current_user.id)
    filter_description = ""
    
    # Если форма валидна, применяем фильтры
    if form.validate():
        query, filter_description = apply_transaction_filters(query, form)
    else:
        filter_description = ""
    
    # Выполняем запрос
    all_transactions = query.all()
    
    total_income = Decimal(str(sum(t.amount for t in all_transactions if t.type == "income")))
    total_expense = Decimal(str(sum(t.amount for t in all_transactions if t.type == "expense")))
    balance = total_income - total_expense
    
    return render_template("transactions/all_transactions.html",
                          title="Все транзакции", 
                          transactions=all_transactions, 
                          total_income=total_income, 
                          total_expense=total_expense,
                          balance=balance,
                          form=form,
                          filter_description=filter_description)  # Добавляем описание фильтров


@transactions_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        amount = form.amount.data
        type = form.type.data
        description = form.description.data
        category_id = form.category_id.data
        date = form.date.data
        
        transaction = Transaction(amount=amount, #type: ignore
                                  type=type, #type: ignore
                                  description=description, #type: ignore
                                  category_id=category_id, #type: ignore
                                  user=current_user, #type: ignore
                                  date=date) #type: ignore
        
        try:
            db.session.add(transaction)
            db.session.commit()
            logger.info("Транзакция создана",
            extra={
                "user_id": current_user.id,
                "transaction_id": transaction.id,
                "amount": amount,
                "type": type,
                "category_id": category_id
            })
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
            logger.error("Возникла непредвиденная ошибка", exc_info=True)
            return render_template("transactions/add.html", form=form)
    else:
        return render_template("transactions/add.html", form=form)
        
        

@transactions_bp.route("/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if not transaction:
        flash("Транзакция не найдена!", "error")
        logger.warning("Попытка найти несуществующую транзакцию",
                     extra={
                         "user_id": current_user.id,
                         "user_username": current_user.username,
                         "ip": request.remote_addr,
                         "url": request.path
                     })
        return redirect(url_for("transactions.transaction_main"))
    form = TransactionForm()
    if transaction.user_id != current_user.id:
        flash("У вас недостаточно прав!", "error")
        logger.warning("Попытка редактирования чужой транзакции",
                        extra={
                         "user_id": current_user.id,
                         "user_username": current_user.username,
                         "transaction_id": transaction.id,
                         "ip": request.remote_addr,
                     })
        return redirect(url_for("transactions.transaction_main"))
    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.type = form.type.data
        transaction.description = form.description.data
        transaction.category_id = form.category_id.data 
        transaction.date = form.date.data
        transaction.user = current_user 
        try:
            db.session.commit()
            logger.info("Успешное изменение транзакции",
                        extra={
                         "user_id": current_user.id,
                         "user_username": current_user.username,
                         "transaction_id": transaction.id,
                         "ip": request.remote_addr
                     })
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
            logger.error("Непредвиденная ошибка при изменении транзакции", exc_info=True)
            return render_template("transactions/edit.html", form=form)
    else:
        if request.method == "GET":
            form.process(obj=transaction)
        return render_template("transactions/edit.html", form=form)


@transactions_bp.route("/<int:transaction_id>/delete", methods=["POST", "GET"])
@login_required
def delete_transaction(transaction_id):
    form = FilterForm()
    
    form = DeleteConfirmForm()
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if not transaction:
        flash("Транзакция не найдена!", "error")
        logger.warning("Попытка найти несуществующую транзакцию",
                     extra={
                         "user_id": current_user.id,
                         "user_username": current_user.username,
                         "ip": request.remote_addr,
                         "url": request.path
                     })
        return redirect(url_for("transactions.transaction_main"))
    if transaction.user_id != current_user.id:
        flash("У вас недостаточно прав!", "error")
        logger.warning("Попытка удаления чужой транзакции",
                        extra={
                         "user_id": current_user.id,
                         "user_username": current_user.username,
                         "transaction_id": transaction.id,
                         "ip": request.remote_addr,
                     })
        return redirect(url_for("transactions.transaction_main"))
    if request.method == "GET":
        return render_template("transactions/delete.html", form=form)
    else:
        delete = form.submit_delete.data
        cancel = form.submit_cancel.data
        if delete:
            try:
                db.session.delete(transaction)
                db.session.commit()
                logger.info("Успешное удаление транзакции",
                            extra={
                                "user_id": current_user.id,
                                "user_username": current_user.username,
                                "url": request.path
                            })
                return redirect(url_for("transactions.transaction_main"))
            except Exception as e:
                db.session.rollback()
                flash("Что-то пошло не так!", "error")
                logger.error("Непредвиденная ошибка при удалении", exc_info=True)
                return redirect(url_for("transactions.transaction_main"))
        elif cancel:
            return redirect(url_for("transactions.transaction_main"))
        else:
            return redirect(url_for("transactions.transaction_main"))
