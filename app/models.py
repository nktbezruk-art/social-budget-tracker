from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from flask_login import UserMixin
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import db


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    username: so.Mapped[str] = so.mapped_column(
        sa.String(120), unique=True, nullable=False
    )
    email: so.Mapped[str] = so.mapped_column(
        sa.String(120), unique=True, nullable=False
    )
    password_hash: so.Mapped[str] = so.mapped_column(
        sa.String(120), nullable=False
    )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.utcnow
    )

    transactions: so.Mapped[List["Transaction"]] = so.relationship(
        back_populates="user"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    amount: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), nullable=False
    )
    type: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)
    description: so.Mapped[str] = so.mapped_column(
        sa.String(100), nullable=False
    )
    date: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.utcnow
    )
    image_filename: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(200), nullable=True
    )

    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey("user.id")
    )
    user: so.Mapped["User"] = so.relationship(back_populates="transactions")

    category_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey("category.id")
    )
    category: so.Mapped["Category"] = so.relationship(
        back_populates="transactions"
    )


class Category(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(120), unique=True, nullable=False
        )

    transactions: so.Mapped[List["Transaction"]] = so.relationship(
        back_populates="category"
    )
