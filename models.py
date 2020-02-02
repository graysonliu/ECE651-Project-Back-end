from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from utils import Serializer


class User(db.Model, Serializer):
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
