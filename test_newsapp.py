import unittest
from contextlib import contextmanager

from flask import request, jsonify, current_app, appcontext_pushed, g
import time

from news_app import app, db
from news_app.auth import generate_token, verify_token
from news_app import errors as e
from news_app.routes import hello, get_user_list, register, get_user_info, update_user_info, \
login, get_news_source, get_news, get_news_by_source
from news_app.commands import init_db, create_admin, update_admin, delete_admin, init_sources
from news_app.models import User, NewsCategory, NewsSource, News
from news_app.utils import Serializer

class NewsappTestCase(unittest.TestCase):
    def setUp(self):
        # set up test enviroment
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
        )
        db.create_all()
        # add one user
        user = User(
            name='test', username='test_user', gender=1,
            faculty='Engineering', department='Electrical and Computer Engineering',
            admin=0
        )
        user.set_password('123')
        db.session.add(user)
        db.session.commit()
        # create test client
        self.client = app.test_client()
        # create test runner
        self.runner = app.test_cli_runner()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # test whether app exist
    def test_app_exist(self):
        print
        self.assertIsNotNone(app)

    # test whether under test
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    def test_home_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('The server is running.', data)

    # test user authorization
    def test_user_login(self):
        # login success
        response = self.client.post('/api/v1/login', json={'username': 'test_user', 'password': '123'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(User.query.get(1), verify_token(json_data['token']))

        # missing password
        response = self.client.post('/api/v1/login', json={'username': 'test_user'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(1006, json_data['error_code'])
        self.assertEqual('Missing data.', json_data['description'])
        # missing username
        response = self.client.post('/api/v1/login', json={'password': '123'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(1006, json_data['error_code'])
        self.assertEqual('Missing data.', json_data['description'])

        # wrong password
        response = self.client.post('/api/v1/login', json={'username': 'test_user', 'password': '456'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(1004, json_data['error_code'])
        self.assertEqual('Authentication failure.', json_data['description'])
        # user not exist
        response = self.client.post('/api/v1/login', json={'username': 'tt', 'password': '123'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(1004, json_data['error_code'])
        self.assertEqual('Authentication failure.', json_data['description'])

    # test user register
    def test_user_register(self):
        # register success
        response = self.client.post('/api/v1/users', json={'username': 'test_user2', 'password': '123'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(User.query.get(2), verify_token(json_data['token']))

        # missing password or username
        response = self.client.post('/api/v1/users', json={'password': '123'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(1006, json_data['error_code'])
        self.assertEqual('Missing data.', json_data['description'])
        response = self.client.post('/api/v1/users', json={'username': 'test_user2'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(1006, json_data['error_code'])
        self.assertEqual('Missing data.', json_data['description'])

        # username exists
        response = self.client.post('/api/v1/users', json={'username': 'test_user', 'password': '123'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(1005, json_data['error_code'])
        self.assertEqual('Existing username.', json_data['description'])

    def test_verify_token(self):
        # token is valid
        token = generate_token(1)
        self.assertEqual(User.query.get(1), verify_token(token))
        # token is None
        with self.assertRaises(e.LoginRequired):
            verify_token(None)
        # token is expired
        token = generate_token(1, 1)
        time.sleep(2)
        with self.assertRaises(e.ExpiredToken):
            verify_token(token)
        # token is invalid
        with self.assertRaises(e.InvalidToken):
            verify_token('wrong token')

    def test_get_user_info(self):
        user = User.query.get(1)
        response = self.client.get('/api/v1/users/1', headers={'token': generate_token(1)})
        json_data = response.get_json()
        self.assertEqual(jsonify(user.serialize()), json_data)



        # @contextmanager
        # def user_set(app, user):
        #     def handler(sender, **kwargs):
        #         g.user = user
        #
        #     with appcontext_pushed.connected_to(handler, app):
        #         yield
        #
        # user = User.query.get(1)
        # with user_set(app, user):
        #     request.headers['token'] = generate_token(1)
        #     response = self.client.get('/api/v1/users/1')
        #     json_data = response.get_json()
        #     self.assertEqual(jsonify(user.serialize()), json_data)



if __name__ == '__main__':
    unittest.main()