from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileSize
from wtforms import (StringField, EmailField, PasswordField,
                     SubmitField, DecimalField, SelectField,
                     DateField, BooleanField)
from wtforms.validators import DataRequired, Email, EqualTo, Optional


class LoginForm(FlaskForm):
    valid_data = StringField("Имя или почта", validators=[
        DataRequired(message="Поле обязательно для заполнения")])
    password = PasswordField("Пароль", validators=[
        DataRequired(message="Поле обязательно для заполнения")])
    remember = BooleanField("Запомнить меня")
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
        ('income', 'Доход'),
        ('expense', 'Расход')
    ])
    description = StringField("Описание")
    category_id = SelectField("Категория", coerce=int)
    date = DateField("Дата", default=datetime.today)
    receipt_image = FileField(
        'Фото чека (опционально)',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!'),
            FileSize(max_size=5 * 1024 * 1024)
        ]
    )
    submit = SubmitField('Создать')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Category
        categories = Category.get_all_cached()
        self.category_id.choices = [(c.id, c.name) for c in categories]


class DeleteConfirmForm(FlaskForm):
    submit_delete = SubmitField('Удалить')
    submit_cancel = SubmitField('Отмена')


class FilterForm(FlaskForm):
    category_id = SelectField(
        "Категория",
        coerce=lambda x: int(x) if x and x != "" else None,
        validators=[Optional()]
        )

    transaction_type = SelectField(
        "Тип",
        choices=[
            ('all', 'Все'),
            ('income', 'Доходы'),
            ('expense', 'Расходы')
        ],
        default='all')

    period = SelectField(
        "Период",
        choices=[
            ("today", "сегодня"),
            ("this_week", "за эту неделю"),
            ("this_month", "за этот месяц"),
            ("last_3_months", "за последние 3 месяца"),
            ("this_year", "за этот год"),
            ("all_time", "за все время")
        ],
        default="today")

    apply_filter = SubmitField("Применить")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Category
        categories = Category.query.all()
        self.category_id.choices = [
            ("", "Все")] + [(c.id, c.name) for c in categories]  # type: ignore
