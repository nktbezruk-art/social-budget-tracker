from datetime import datetime, time
from flask import url_for, redirect, render_template, session, flash, request
from flask_login import current_user, login_required
from . import transactions_bp
from app import db
from app.models import Transaction, User
from app.forms import TransactionForm, DeleteConfirmForm, FilterForm


#1. ФИКС БАГОВ (сначала это)
#   - Исправить фильтр по категории (значение "None" в URL)
#   - Починить фильтр по месяцу (декабрь = 13 месяц)
#   - Убрать дублирующий код фильтрации

#2. ДОБАВИТЬ НОВЫЕ ФИЛЬТРЫ (если успеем)
#   - Категория (работает, но нужно исправить значение)
#   - Месяц (работает частично, нужно исправить)
#   - Конкретная дата (приоритет над месяцем)

#3. ПАГИНАЦИЯ (базовая)
#   - Ограничение 50 транзакций на странице
#   - Кнопки "Назад"/"Вперед" если транзакций много
#   - Сохранение фильтров при пагинации

#4. УЛУЧШЕНИЯ UX
#   - Сделать форму фильтров всплывающей (<details>)
#   - Показывать активные фильтры (текстом над списком)
#   - Добавить сброс отдельных фильтров

@transactions_bp.route("/")
@login_required
def transaction_main():
    form = FilterForm(request.args)
    
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if form.validate():
        if form.transaction_type.data != 'all':
            query = query.filter(Transaction.type == form.transaction_type.data)
    
    all_transactions = query.all()
    total_income = sum(t.amount for t in all_transactions if t.type =="income")
    total_expense = sum(t.amount for t in all_transactions if t.type =="expense")
    balance = total_income - total_expense
    
    return render_template("transactions/all_transactions.html",
                          title="Все транзакции", 
                          transactions=all_transactions, 
                          total_income=total_income, 
                          total_expense=total_expense,
                          balance=balance,
                          form=form)
    


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
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
            return render_template("transactions/add.html", form=form)
    else:
        return render_template("transactions/add.html", form=form)
        
        

@transactions_bp.route("/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if not transaction:
        flash("Транзакция не найдена!", "error")
        return redirect(url_for("transactions.transaction_main"))
    form = TransactionForm()
    if transaction.user_id != current_user.id:
        flash("У вас недостаточно прав!", "error")
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
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
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
        return redirect(url_for("transactions.transaction_main"))
    if transaction.user_id != current_user.id:
        flash("У вас недостаточно прав!", "error")
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
                return redirect(url_for("transactions.transaction_main"))
            except Exception as e:
                db.session.rollback()
                flash("Что-то пошло не так!", "error")
                return redirect(url_for("transactions.transaction_main"))
        elif cancel:
            return redirect(url_for("transactions.transaction_main"))
        else:
            return redirect(url_for("transactions.transaction_main"))
