from flask import request, abort, jsonify
from models import User
from app import app, db
from auth import generate_token, admin_required, login_required


@app.route('/')
def hello():
    return 'The server is running.'


@app.route('/api/v1/users', methods=['GET'])
@admin_required
def get_user_list():
    user_list = User.query.all()
    return jsonify(user_list=User.serialize_list(user_list))


@app.route('/api/v1/users', methods=['POST'])
def register():
    name = request.json.get('name')
    username = request.json.get('username')
    password = request.json.get('password')
    gender = request.json.get('gender')
    if username is None or password is None:
        abort(400, description="missing username or password")
    if User.query.filter_by(username=username).first() is not None:
        abort(409, description="existing username")
    user = User(name=name, username=username, gender=gender, admin=False)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    user = User.query.filter_by(username=username).first()
    return jsonify(id=user.id, token=generate_token(user.id)), 201


@app.route('/api/v1/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400, description="missing username or password")
    user = User.query.filter_by(username=username).first()
    if user is None or not user.verify_password(password):
        abort(401, description="wrong username or password")
    return jsonify(id=user.id, token=generate_token(user.id))
