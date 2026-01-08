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

    return app
