import click
from datetime import timedelta, datetime

from flask import current_app  # noqa: F401, E402

from app.db import db


def register_commands(app):
    @app.cli.command("cleanup-old-transactions")
    @click.option("--days", default=365, help="Удалить старше N дней")
    @click.option(
        "--dry-run",
        is_flag=True,
        help="Показать что удалит, но не удалять",
    )
    def cleanup_old_transaction(days, dry_run):
        """Удаление транзакций старше N дней, по умолчанию - 365"""
        from app.models import Transaction

        cutoff_date = datetime.now() - timedelta(days=days)
        query = Transaction.query.filter(Transaction.date < cutoff_date)
        old_transactions = query.all()

        if old_transactions:
            if dry_run:
                click.echo("Транзакции, которые будут удалены:")
                for transaction in old_transactions:
                    click.echo(
                        f"{transaction.type} {str(transaction.amount)} "
                        f"{transaction.date.strftime('%d.%m.%Y %H:%M')}"
                    )
            else:
                count = query.delete()
                db.session.commit()
                click.secho(f"✅ Удалено {str(count)} транзакций", fg="green")

        else:
            click.echo("Транзакций нет")

    @app.cli.command("add-categories")
    @click.argument("categories", nargs=-1)
    @click.option("--details", "-d", is_flag=True, help="Детальный вывод")
    def add_category(categories, details):
        from app.models import Category

        added = 0
        existed = 0

        for name in categories:
            name = name.strip().capitalize()
            category = Category.query.filter_by(name=name).first()
            if category:
                existed += 1
                if details:
                    click.echo(
                        f"⏭️ Категория '{category.name}' уже существует"
                    )
            else:
                added += 1
                category = Category(name=name)  # type: ignore
                db.session.add(category)
                if details:
                    click.secho(f"✅ Категория {name} добавлена!", fg="green")

        db.session.commit()
        if added > 0:
            click.secho(
                f"🎯 Добавлено {added} категорий", fg="green", bold=True
            )
        if existed > 0:
            click.echo(f"⏭️  Пропущено {existed} существующих категорий")
