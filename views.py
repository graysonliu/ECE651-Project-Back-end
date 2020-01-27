from flask import request, Blueprint
from models import User
from app import db

blueprint = Blueprint('blueprint', __name__)


@blueprint.route('/')
def hello():
    return 'Hello'


@blueprint.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User(username=username, password=password)
    try:
        db.session.add(user)
        db.session.commit()
        return 'successful'
    except Exception as e:
        print('\n' + str(e))
        return 'failed'
