from app import app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, \
    BadSignature, SignatureExpired
from models import User
import functools
import os
from flask import request, abort


def generate_token(user_id, expiration=3600):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': user_id}).decode("utf-8")


def verify_token(token):
    if os.environ.get('FLASK_ENV') == 'development' and token == 'admin':  # for testing in development environment
        return 'admin'
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None  # expired token
    except BadSignature:
        return None  # invalid token
    user = User.query.get(data['id'])
    return user


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        token = request.headers.get('token')
        if token is None:
            abort(401, description="login required")
        user = verify_token(token)
        if user is None:
            abort(401, description="invalid or expired session")
        if user == 'admin' or user.admin:
            return func(*args, **kw)
        if user.id == kw['user_id']:
            return func(*args, **kw)
        else:  # deny access to content of other users
            abort(401, description="no permission")

    return wrapper


def admin_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        token = request.headers.get('token')
        if token is None:
            abort(401, description="login required")
        user = verify_token(token)
        if user is None:
            abort(401, description="invalid or expired session")
        if user == 'admin' or user.admin:
            return func(*args, **kw)
        else:  # deny access to content of admin
            abort(401, description="no permission")

    return wrapper


def login_for_custom_content(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        token = request.headers.get('token')
        if token is None:
            return func(*args, **kw)

    return wrapper
