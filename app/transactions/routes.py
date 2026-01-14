import logging
import os
import uuid
from decimal import Decimal

from flask import (
    url_for,
    redirect,
    render_template,
    flash,
    request,
)
from flask_login import current_user, login_required

from . import transactions_bp
from app import db
from app.models import Transaction
from app.forms import TransactionForm, DeleteConfirmForm, FilterForm

logger = logging.getLogger(__name__)


def save_receipt_image(file):
    """Сохраняет изображение чека и возвращает имя файла."""
    if not file or file.filename == "":
        return None

    if "." in file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif"]:
            return None
    else:
        return None

    filename = f"{uuid.uuid4()}.{ext}"

    # Создаем папки от корня проекта
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_folder = os.path.join(base_dir, "static", "uploads", "transactions")

    # Гарантируем что папки существуют
    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(upload_folder, filename)

    try:
        file.save(filepath)
        logger.info(f"Файл сохранен: {filepath}")
        return filename
    except Exception as e:
        logger.error(f"Ошибка сохранения файла: {str(e)}")
        return None


def delete_receipt_image(filename):
    """Удаляет изображение чека."""
    if not filename:
        return

    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(
        base_dir, "static", "uploads", "transactions", filename)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Файл удален: {filepath}")
    except Exception as e:
        logger.error(f"Ошибка удаления файла {filename}: {str(e)}")


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
        query = query.filter(
            Transaction.date >= today, Transaction.date < tomorrow
        )
        description_parts.append("сегодня")

    elif period == "this_week":
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        query = query.filter(
            Transaction.date >= monday, Transaction.date < tomorrow
        )
        description_parts.append("за эту неделю")

    elif period == "this_month":
        first_of_the_month = date(today.year, today.month, 1)
        query = query.filter(
            Transaction.date >= first_of_the_month,
            Transaction.date < tomorrow,
        )
        description_parts.append("за этот месяц")

    elif period == "last_3_months":
        three_month_ago = today - timedelta(days=90)
        query = query.filter(
            Transaction.date >= three_month_ago, Transaction.date < tomorrow
        )
        description_parts.append("за последние 3 месяца")

    elif period == "this_year":
        first_of_the_year = date(today.year, 1, 1)
        query = query.filter(
            Transaction.date >= first_of_the_year, Transaction.date < tomorrow
        )
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
    query = Transaction.query.filter_by(user_id=current_user.id)
    filter_description = ""

    if form.validate():
        query, filter_description = apply_transaction_filters(query, form)
    else:
        filter_description = ""

    all_transactions = query.all()

    total_income = Decimal(
        str(sum(t.amount for t in all_transactions if t.type == "income"))
    )
    total_expense = Decimal(
        str(sum(t.amount for t in all_transactions if t.type == "expense"))
    )
    balance = total_income - total_expense

    return render_template(
        "transactions/all_transactions.html",
        title="Все транзакции",
        transactions=all_transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        form=form,
        filter_description=filter_description,
    )


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

        image_filename = None
        if form.receipt_image.data:
            image_filename = save_receipt_image(form.receipt_image.data)
            if image_filename is None:
                flash("Ошибка при сохранении изображения", "error")
                return render_template("transactions/add.html", form=form)

        transaction = Transaction(
            amount=amount,
            type=type,
            description=description,
            category_id=category_id,
            user=current_user,
            date=date,
            image_filename=image_filename,
        )

        try:
            db.session.add(transaction)
            db.session.commit()
            logger.info(
                "Транзакция создана",
                extra={
                    "user_id": current_user.id,
                    "transaction_id": transaction.id,
                    "amount": amount,
                    "type": type,
                    "category_id": category_id,
                    "has_image": image_filename is not None,
                },
            )
            return redirect(url_for("transactions.transaction_main"))
        except Exception:
            db.session.rollback()
            if image_filename:
                delete_receipt_image(image_filename)
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
        logger.warning(
            "Попытка найти несуществующую транзакцию",
            extra={
                "user_id": current_user.id,
                "user_username": current_user.username,
                "ip": request.remote_addr,
                "url": request.path,
            },
        )
        return redirect(url_for("transactions.transaction_main"))

    form = TransactionForm()

    if transaction.user_id != current_user.id:
        flash("У вас недостаточно прав!", "error")
        logger.warning(
            "Попытка редактирования чужой транзакции",
            extra={
                "user_id": current_user.id,
                "user_username": current_user.username,
                "transaction_id": transaction.id,
                "ip": request.remote_addr,
            },
        )
        return redirect(url_for("transactions.transaction_main"))

    if form.validate_on_submit():
        old_image_filename = transaction.image_filename

        if form.receipt_image.data:
            new_image_filename = save_receipt_image(form.receipt_image.data)
            if new_image_filename is not None:
                transaction.image_filename = new_image_filename
                if old_image_filename and (
                    old_image_filename != new_image_filename
                ):
                    delete_receipt_image(old_image_filename)

        transaction.amount = form.amount.data
        transaction.type = form.type.data
        transaction.description = form.description.data
        transaction.category_id = form.category_id.data
        transaction.date = form.date.data

        try:
            db.session.commit()
            logger.info(
                "Успешное изменение транзакции",
                extra={
                    "user_id": current_user.id,
                    "user_username": current_user.username,
                    "transaction_id": transaction.id,
                    "ip": request.remote_addr,
                    "image_updated": form.receipt_image.data is not None,
                },
            )
            return redirect(url_for("transactions.transaction_main"))
        except Exception:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
            logger.error(
                "Непредвиденная ошибка при изменении транзакции",
                exc_info=True,
            )
            return render_template(
                "transactions/edit.html", form=form, transaction=transaction
            )
    else:
        if request.method == "GET":
            form.process(obj=transaction)
        return render_template(
            "transactions/edit.html", form=form, transaction=transaction
        )


@transactions_bp.route("/<int:transaction_id>")
@login_required
def view_transaction(transaction_id):
    """Детальный просмотр транзакции с изображением."""
    transaction = Transaction.query.filter_by(id=transaction_id).first()

    if not transaction:
        flash("Транзакция не найдена!", "error")
        logger.warning(
            "Попытка найти несуществующую транзакцию",
            extra={
                "user_id": current_user.id,
                "user_username": current_user.username,
                "ip": request.remote_addr,
                "url": request.path,
            },
        )
        return redirect(url_for("transactions.transaction_main"))

    if transaction.user_id != current_user.id:
        flash("У вас недостаточно прав!", "error")
        logger.warning(
            "Попытка просмотра чужой транзакции",
            extra={
                "user_id": current_user.id,
                "user_username": current_user.username,
                "transaction_id": transaction.id,
                "ip": request.remote_addr,
            },
        )
        return redirect(url_for("transactions.transaction_main"))

    logger.info(
        "Просмотр транзакции",
        extra={
            "user_id": current_user.id,
            "transaction_id": transaction.id,
        },
    )

    return render_template(
        "transactions/detail.html",
        title="Детали транзакции",
        transaction=transaction,
    )


@transactions_bp.route("/<int:transaction_id>/delete", methods=["POST", "GET"])
@login_required
def delete_transaction(transaction_id):
    form = DeleteConfirmForm()
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if not transaction:
        flash("Транзакция не найдена!", "error")
        logger.warning(
            "Попытка найти несуществующую транзакцию",
            extra={
                "user_id": current_user.id,
                "user_username": current_user.username,
                "ip": request.remote_addr,
                "url": request.path,
            },
        )
        return redirect(url_for("transactions.transaction_main"))

    if transaction.user_id != current_user.id:
        flash("У вас недостаточно прав!", "error")
        logger.warning(
            "Попытка удаления чужой транзакции",
            extra={
                "user_id": current_user.id,
                "user_username": current_user.username,
                "transaction_id": transaction.id,
                "ip": request.remote_addr,
            },
        )
        return redirect(url_for("transactions.transaction_main"))

    if request.method == "GET":
        return render_template(
            "transactions/delete.html", form=form, transaction=transaction
        )
    else:
        delete = form.submit_delete.data
        cancel = form.submit_cancel.data

        if delete:
            image_filename = transaction.image_filename

            try:
                db.session.delete(transaction)
                db.session.commit()

                if image_filename:
                    delete_receipt_image(image_filename)

                logger.info(
                    "Успешное удаление транзакции",
                    extra={
                        "user_id": current_user.id,
                        "user_username": current_user.username,
                        "url": request.path,
                        "had_image": image_filename is not None,
                    },
                )
                return redirect(url_for("transactions.transaction_main"))
            except Exception:
                db.session.rollback()
                flash("Что-то пошло не так!", "error")
                logger.error(
                    "Непредвиденная ошибка при удалении", exc_info=True
                )
                return redirect(url_for("transactions.transaction_main"))
        elif cancel:
            return redirect(url_for("transactions.transaction_main"))
        else:
            return redirect(url_for("transactions.transaction_main"))
