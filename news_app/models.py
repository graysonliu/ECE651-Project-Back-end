from news_app import db
from werkzeug.security import generate_password_hash, check_password_hash
from news_app.utils import Serializer


class User(db.Model, Serializer):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.Integer)
    admin = db.Column(db.Boolean, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def serialize(self):
        exclude = ['password_hash', 'admin']
        d = Serializer.serialize(self)
        [d.pop(attr, None) for attr in exclude]
        return d


class NewsCategory(db.Model, Serializer):
    __tablename__ = "NewsCategory"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024), nullable=False)


class NewsSource(db.Model, Serializer):
    __tablename__ = "NewsSource"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(1024), nullable=False)
    name = db.Column(db.String(1024), nullable=False)
