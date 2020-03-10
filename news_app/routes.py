from flask import request, jsonify
from news_app.models import *
from news_app import app, db
from news_app import errors as e
from news_app.auth import generate_token, admin_required, login_required, login_for_custom_content
from sqlalchemy.sql import text


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
    faculty = request.json.get('faculty')
    department = request.json.get('department')
    following = request.json.get('following')
    if username is None or password is None:
        raise e.MissingData()
    if User.query.filter_by(username=username).first():
        raise e.ExistingUsername()
    user = User(name=name, username=username, gender=gender, admin=False, faculty=faculty, department=department,
                following=following)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    user = User.query.filter_by(username=username).first()
    return jsonify(id=user.id, token=generate_token(user.id)), 201


@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_info(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.serialize())


@app.route('/api/v1/users/<int:user_id>', methods=['PATCH'])
@login_required
def update_user_info(user_id):
    user = User.query.get_or_404(user_id)

    # change password
    old_password = request.json.get('old_password')
    if old_password is not None:
        if not user.verify_password(old_password):
            raise e.AuthenticationFailure()
        new_password = request.json.get('new_password')
        if new_password is None:
            raise e.MissingData()
        user.set_password(new_password)

    # change username
    username = request.json.get('username')
    if username is not None:
        if username != user.username and User.query.filter_by(username=username).first():
            raise e.ExistingUsername()
        user.username = username

    # change other information
    patch_attr = ['name', 'gender', 'faculty', 'department', 'following']
    for attr in patch_attr:
        value = request.json.get(attr)
        if value is not None:
            user.__setattr__(attr, value)
    db.session.commit()
    return 'Success'


@app.route('/api/v1/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        raise e.MissingData()
    user = User.query.filter_by(username=username).first()
    if user is None or not user.verify_password(password):
        raise e.AuthenticationFailure()
    return jsonify(id=user.id, token=generate_token(user.id))


@app.route('/api/v1/news-source', methods=['GET'])
def get_news_source():
    news_source_list = NewsCategory.query.all()
    return jsonify(news_source_list=NewsCategory.serialize_list(news_source_list))


@app.route('/api/v1/news', methods=['GET'])
@login_for_custom_content
def get_news(user_id=None):
    page_size = 10
    page = request.args.get('page', default=1, type=int)

    def get_latest_news_from_all_sources():
        news = News.query.order_by(News.date.desc()).slice((page - 1) * page_size, page * page_size).all()
        return jsonify(news=News.serialize_list(news))

    if user_id is None:
        return get_latest_news_from_all_sources()
    else:
        following = User.query.filter_by(id=user_id).first().following
        if following is None or following.strip() == '':
            return get_latest_news_from_all_sources()
        sources = following.strip().split(',')
        where_str = str()
        for i, source in enumerate(sources):
            source_id = int(source.strip())
            where_str = where_str + 'source_id=%d' % source_id
            if i != len(sources) - 1:
                where_str = where_str + ' or '
        news = News.query.filter(text(where_str)).order_by(News.date.desc()).slice((page - 1) * page_size,
                                                                                   page * page_size).all()
        return jsonify(news=News.serialize_list(news))


@app.route('/api/v1/news/<int:source_id>', methods=['GET'])
def get_news_by_source(source_id):
    page_size = 10
    page = request.args.get('page', default=1, type=int)
    news = News.query.filter_by(source_id=source_id).order_by(News.date.desc()).slice((page - 1) * page_size,
                                                                                      page * page_size).all()
    return jsonify(news=News.serialize_list(news))
