from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from typing import List
from flask_login import UserMixin
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import db

friends_association = sa.Table(
    "friends_association",
    db.metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True),
    sa.Column("friend_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
)


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True, nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True, nullable=False)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True, nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
    
    transactions: so.Mapped[List["Transaction"]] = so.relationship(back_populates="user")
    friends: so.Mapped[List["User"]] = so.relationship(
        secondary = friends_association,
        primaryjoin=(id == friends_association.c.user_id),
        secondaryjoin=(id == friends_association.c.friend_id),
        lazy = "dynamic"
    )
    comments: so.Mapped[List["Comment"]] = so.relationship(back_populates="author")
    posts: so.Mapped[List["Post"]] = so.relationship(back_populates="author") 
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    amount: so.Mapped[Decimal] = so.mapped_column(sa.Numeric, nullable=False)
    type: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)
    description: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    date: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
    
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey("user.id"))
    user: so.Mapped["User"] = so.relationship(back_populates="transactions")
    
    category_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey("category.id"))
    category: so.Mapped["Category"] = so.relationship(back_populates="transactions")


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(120), nullable=False)
    content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
    
    author_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey("user.id"))
    author: so.Mapped["User"] = so.relationship(back_populates="posts")
    
    comments: so.Mapped[List["Comment"]] = so.relationship(back_populates="post")
    
    
    
class Category(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True, nullable=False)
    
    transactions: so.Mapped[List["Transaction"]] = so.relationship(back_populates="category")


class Comment(db.Model):
     id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
     content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
     created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
     
     post_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey("post.id"))
     post: so.Mapped["Post"] = so.relationship(back_populates="comments")
     
     author_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey("user.id"))
     author: so.Mapped["User"] = so.relationship(back_populates="comments")
     
     