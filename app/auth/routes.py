from app.models import User
from . import auth_bp
from flask import url_for, redirect, render_template, request, flash, session
from app.db import db
from flask_login import login_user, logout_user, current_user, login_required


@auth_bp.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        valid_data = request.form.get("valid_data")
        password = request.form.get("password")
        
        if not (valid_data and password):
            flash("Необходимо заполнить все поля!", "error")
            return redirect(url_for("auth.login"))
        
        user = User.query.filter_by(username=valid_data).first() or User.query.filter_by(email=valid_data).first()
        if not (user and user.check_password(password)):
            flash("Неверные данные!", "error")
            return redirect(url_for("auth.login"))
        
        try:
            login_user(user)
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
            return redirect(url_for("auth.login"))
    
    
        


@auth_bp.route("/register", methods = ["POST", "GET"])
def registration():
    if request.method == "GET":
        return render_template("register.html")
    
    else:
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if not all(item for item in [username, email, password, confirm_password]):
            flash("Необходимо заполнить все поля!", "error")
            return redirect(url_for("auth.register"))
        
        if not email or "@" not in email or "." not in email:
            flash("Необходимо ввести правильный email!", "error")
            return redirect(url_for("auth.register"))
        
        if password != confirm_password:
            flash("Пароли должны совпадать!", "error")
            return redirect(url_for("auth.register"))
        
        if User.query.filter_by(username=username).first():
            flash("Такое имя уже занято!", "error")
            return redirect(url_for("auth.register"))
        
        if User.query.filter_by(email=email).first():
            flash("Такая почта уже занята!", "error")
            return redirect(url_for("auth.register"))
        
        user = User(username=username, email=email) #type: ignore
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("transactions.transaction_main"))
        except Exception as e:
            db.session.rollback()
            flash("Что-то пошло не так!", "error")
            return redirect(url_for("auth.register"))


@login_required
@auth_bp.route("/logout")
def logout():
    user = current_user()
    logout_user()
    flash("Вы успешно вышли из аккаунта!", "success")
    return redirect(url_for("auth.login"))