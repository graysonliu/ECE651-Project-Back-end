from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(db.Model):
    __tablename__ = 'user'
    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(20))
