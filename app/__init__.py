import os
import logging

from flask import Flask, request, render_template

from config import ProductionConfig, DevelopmentConfig, TestConfig
from app.db import db, migrate, login_manager, csrf, jwt


def create_app():
    app = Flask(__name__)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    logger = logging.getLogger("app")
    logger.info("Social Budget Tracker application starting...")
    logger.info("Server starting at http://127.0.0.1:5000")
    logging.getLogger("werkzeug").disabled = True

    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("flask_wtf").setLevel(logging.WARNING)

    config_name = os.environ.get("FLASK_ENV", "development")

    if config_name == "development":
        app.config.from_object(DevelopmentConfig)
    elif config_name == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(TestConfig)

    app.config["RESTFUL_JSON"] = {"ensure_ascii": False}

    if not os.environ.get("SECRET_KEY", ""):
        raise ValueError("SECRET_KEY must be set in .env file")

    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)

    from app import models  # noqa: F401, E402

    from app.auth import auth_bp
    from app.transactions import transactions_bp
    from app.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)

    def register_errorhandlers(app):
        @app.errorhandler(404)
        def error_404(error):
            logger.warning(
                "Ошибка 404",
                extra={
                    "url": request.path,
                    "ip": request.remote_addr,
                    "request_method": request.method,
                },
            )
            return render_template("errors/404.html", title="Ошибка 404"), 404

        @app.errorhandler(500)
        def error_500(error):
            logger.error("Ошибка 500", exc_info=True)
            return render_template("errors/500.html", title="Ошибка 500"), 500

    register_errorhandlers(app)

    from app import commands

    commands.register_commands(app)

    from app.api import api_bp

    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)

    # Контекстный процессор для работы с загрузками файлов
    @app.context_processor
    def utility_processor():
        """Добавляет вспомогательные функции в контекст всех шаблонов."""
        def get_transaction_image_url(filename):
            """Возвращает полный URL для изображения транзакции."""
            if not filename:
                return None
            return f"/static/uploads/transactions/{filename}"

        def transaction_has_image(transaction):
            """Проверяет, есть ли у транзакции изображение."""
            return (
                hasattr(transaction, 'image_filename') and
                transaction.image_filename
            )

        return dict(
            get_transaction_image_url=get_transaction_image_url,
            transaction_has_image=transaction_has_image,
        )

    # Создаем папку для загрузок при старте приложения
    with app.app_context():
        if app.static_folder:
            uploads_dir = os.path.join(
                app.static_folder, 'uploads', 'transactions'
            )
            os.makedirs(uploads_dir, exist_ok=True)
            logger.info(f"Папка для загрузок создана: {uploads_dir}")

    return app
