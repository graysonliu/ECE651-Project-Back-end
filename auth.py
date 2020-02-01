from app import app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, \
    BadSignature, SignatureExpired
from models import User
import functools
from flask import request, abort


def generate_token(user_id, expiration=3600):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': user_id}).decode("utf-8")


def verify_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None  # expired token
    except BadSignature:
        return None  # invalid token
    user = User.query.get(data['id'])
    return user


def admin_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        token = request.headers.get('token')
        user = verify_token(token)
        if user is None or not user.admin:
            abort(401)
        return func(*args, **kw)

    return wrapper


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        token = request.headers.get('token')
        user = verify_token(token)
        if user is None:
            abort(401)
        return func(*args, **kw)

    return wrapper
