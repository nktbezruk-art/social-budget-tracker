from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, DecimalField, SelectField, DateField
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
    
class TransactionForm(FlaskForm):
    amount = DecimalField("Величина", validators=[
        DataRequired(message="Поле обязательно для заполнения")])
    
    type = SelectField("Тип", choices=[
    ('income', 'Доход'),      # 'income' в БД, 'Доход' в интерфейсе  
    ('expense', 'Расход')     # 'expense' в БД, 'Расход' в интерфейсе
])
    
    description = StringField("Описание")
    category_id = SelectField("Категория", coerce=int)
    date = DateField("Дата", default=datetime.today)
    submit = SubmitField('Создать')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Category
        categories = Category.query.all()
        self.category_id.choices = [(c.id, c.name) for c in categories]

class DeleteConfirmForm(FlaskForm):
    submit_delete = SubmitField('Удалить')
    submit_cancel = SubmitField('Отмена')