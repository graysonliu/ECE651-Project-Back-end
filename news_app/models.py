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
    faculty = db.Column(db.String(128))
    department = db.Column(db.String(128))
    following = db.Column(db.String(1000))
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

    def serialize(self):
        exclude = []
        d = Serializer.serialize(self)
        [d.pop(attr, None) for attr in exclude]
        d['sources'] = NewsSource.serialize_list(self.sources, uw_style=1)
        return d


class NewsSource(db.Model, Serializer):
    __tablename__ = "NewsSource"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(1024), nullable=False)
    name = db.Column(db.String(1024), nullable=False)
    uw_style = db.Column(db.Boolean, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('NewsCategory.id', ondelete='CASCADE'))
    category = db.relationship('NewsCategory', backref=db.backref('sources'))

    def serialize(self):
        exclude = ['url', 'uw_style', 'category_id', 'category']
        d = Serializer.serialize(self)
        [d.pop(attr, None) for attr in exclude]
        return d


class News(db.Model, Serializer):
    __tablename__ = "News"
    url = db.Column(db.String(256), primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('NewsSource.id', ondelete='CASCADE'), primary_key=True)
    source = db.relationship('NewsSource')
    title = db.Column(db.String(512))
    abstract = db.Column(db.String(2048))
    image_url = db.Column(db.String(256))
    date = db.Column(db.Date, index=True)

    def serialize(self):
        d = Serializer.serialize(self)
        d['source'] = self.source.name
        return d
