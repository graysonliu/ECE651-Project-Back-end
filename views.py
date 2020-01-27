from flask import Blueprint

blueprint = Blueprint('blueprint', __name__)


@blueprint.route('/')
def hello():
    return 'Hello'


@blueprint.route('/signup')
def signup():
    return 'Hello'
