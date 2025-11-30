from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

class LoginForm(FlaskForm):
    valid_data = StringField("Имя или почта", validators=[
        DataRequired(message="Поле обязательно для заполнения")])
    
    password = PasswordField("Пароль", validators=[
        DataRequired(message="Поле обязательно для заполнения")])
        
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField("Имя", validators=[
        DataRequired(message="Поле обязательно для заполнения")])
    
    email = EmailField("Почта", validators=[
        DataRequired(message="Поле обязательно для заполнения"),
        Email(message="Некорректный email адрес")])
    
    password = PasswordField("Пароль", validators=[
        DataRequired(message="Поле обязательно для заполнения")])
    
    confirm_password = PasswordField("Подтвердите пароль", validators=[
        DataRequired(message="Поле обязательно для заполнения"),
        EqualTo('password', message="Пароли должны совпадать")])
    
    submit = SubmitField('Зарегестрироваться')