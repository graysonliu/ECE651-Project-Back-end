from app import db


class User(db.Model):
    __tablename__ = 'user'
    username = db.Column(db.String(20), primary_key=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
