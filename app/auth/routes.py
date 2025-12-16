import logging
from app.models import User
from . import auth_bp
from flask import url_for, redirect, render_template, request, flash, session
from app.db import db
from flask_login import login_user, logout_user, current_user, login_required
from app.forms import RegistrationForm, LoginForm

logger = logging.getLogger(__name__)

@auth_bp.route("/login", methods = ["POST", "GET"])
def login():
    logger.info("Страница входа открыта")
    form = LoginForm()
    if form.validate_on_submit():
        valid_data = form.valid_data.data
        password = form.password.data
        user = User.query.filter_by(username=valid_data).first() or User.query.filter_by(email=valid_data).first()
        if not (user and user.check_password(password)):
            flash("Неверные данные!", "error")
            logger.warning("Пользователь ввел неверные данные",
                        extra={"ip": request.remote_addr,
                               "url": request.path,
                               "attempted_data": valid_data,
                               "user_agent": request.user_agent.string[:100] })
            return render_template("auth/login.html", form=form, title="Login")
        
        try:
            login_user(user, remember=form.remember.data)
            logger.info("Успешный вход",
                        extra={"ip": request.remote_addr,
                               "url": request.path,
                               "user_id": user.id,
                               "username": user.username})
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            flash("Что-то пошло не так!", "error")
            logger.error("Неудачная попытка входа", exc_info=True)
            return render_template("auth/login.html", form=form, title="Login")

    else:
        return render_template("auth/login.html", form=form, title="Login")
    
    
@auth_bp.route("/register", methods = ["POST", "GET"])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        if User.query.filter_by(username=username).first():
            flash("Такое имя уже занято!", "error")
            logger.warning("Попытка регистрации по существующему имени",
                        extra={"ip": request.remote_addr,
                               "attempted_username": username,
                               "user_agent": request.user_agent.string[:100]})
            return render_template("auth/register.html", form=form, title="Registration")
        
        if User.query.filter_by(email=email).first():
            flash("Такая почта уже занята!", "error")
            logger.warning("Попытка регистрации по существующему email",
                        extra={"ip": request.remote_addr,
                               "attempted_email": email,
                               "user_agent": request.user_agent.string[:100]})
            return render_template("auth/register.html", form=form, title="Registration")
        
        user = User(username=username, email=email) #type: ignore
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            logger.info("Успешная регистрация",
                        extra={"ip": request.remote_addr,
                               "user_id": user.id,
                               "username": user.username})
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
            logger.error("Неудачная попытка регистрации", exc_info=True)
            return render_template("auth/register.html", form=form, title="Registration")
    else:
        return render_template("auth/register.html", form=form, title="Registration")


@auth_bp.route("/logout")
@login_required
def logout():
    user = current_user
    flash("Вы успешно вышли из аккаунта!", "success")
    logger.info("Пользователь вышел из аккаунта",
                extra={"user_id": user.id,
                       "username": user.username,
                       "ip": request.remote_addr})
    logout_user()
    return redirect(url_for("auth.login"))