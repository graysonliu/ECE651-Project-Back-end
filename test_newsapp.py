import unittest
import time
from datetime import datetime
from flask import request, jsonify, current_app, appcontext_pushed, g


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
        db.create_all()  # create database and all tables

        # insert two users
        user1 = User(
            name='test', username='test_user', gender=1,
            faculty='Engineering', department='Electrical and Computer Engineering',
            admin=0, following='1'
        )
        user1.set_password('123')

        user2 = User(
            name='test', username='test_user2', gender=1,
            faculty='Engineering', department='Electrical and Computer Engineering',
            admin=0
        )
        user2.set_password('123')

        # insert news category
        category1 = NewsCategory(id=1, name='University')
        category2 = NewsCategory(id=2, name='Faculties')

        # insert news source
        source1 = NewsSource(url='https://uwaterloo.ca/news/news', name='Waterloo News', uw_style=1, category_id=1)
        source2 = NewsSource(url='https://uwaterloo.ca/engineering/news', name='Engineering', uw_style=1, category_id=2)

        # insert news
        news1 = News(url='https://uwaterloo.ca/library/news/library-and-w-print-make-good-buddies', source_id=1,
                    title='The Library and W Print make good buddies', date=datetime(2019, 11, 22))
        news2 = News(url='https://uwaterloo.ca/applied-health-sciences/news/storytelling-can-reduce-vr-cybersickness', source_id=2,
                     title='Storytelling can reduce VR cybersickness', date=datetime(2020, 2, 12))

        db.session.add_all([user1, user2, category1, category2, source1, source2, news1, news2])
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

# ******************* test auth.py ******************* #
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

# ******************* test routes.py ******************* #
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
        response = self.client.post('/api/v1/users', json={'username': 'test_user3', 'password': '123'},
                                    follow_redirects=True)
        json_data = response.get_json()
        self.assertEqual(User.query.get(3), verify_token(json_data['token']))

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

    def test_get_user_info(self):
        # hold own token to access own profile
        user = User.query.get(1)
        response = self.client.get('/api/v1/users/1', headers={'token': generate_token(1)})
        json_data = response.get_json()
        self.assertEqual(user.serialize(), json_data)

    def test_update_user_info(self):
        # change password
        # old password is wrong
        response = self.client.patch('/api/v1/users/1', headers={'token': generate_token(1)},
                                     json={'old_password': '456', 'new_password': '222'})
        json_data = response.get_json()
        self.assertEqual(1004, json_data['error_code'])
        self.assertEqual('Authentication failure.', json_data['description'])
        # new password is None
        response = self.client.patch('/api/v1/users/1', headers={'token': generate_token(1)},
                                     json={'old_password': '123'})
        json_data = response.get_json()
        self.assertEqual(1006, json_data['error_code'])
        # change password success
        response = self.client.patch('/api/v1/users/1', headers={'token': generate_token(1)},
                                     json={'old_password': '123', 'new_password': '222'})
        user = User.query.get(1)
        self.assertTrue(user.verify_password('222'))

        # change username
        # new username is existed
        response = self.client.patch('/api/v1/users/1', headers={'token': generate_token(1)},
                                     json={'username': 'test_user2'})
        json_data = response.get_json()
        self.assertEqual(1005, json_data['error_code'])
        # change username success
        response = self.client.patch('/api/v1/users/1', headers={'token': generate_token(1)},
                                     json={'username': 'new_username'})
        user = User.query.get(1)
        self.assertEqual(user.username, 'new_username')

        # change ['name', 'gender', 'faculty', 'department', 'following']
        response = self.client.patch('/api/v1/users/1', headers={'token': generate_token(1)},
                                     json={'gender': 0, 'faculty': 'Arts', 'department': 'Communication Arts',
                                           'following': '[1, 2, 3]'})
        user = User.query.get(1)
        self.assertEqual(user.faculty, 'Arts')
        self.assertEqual(user.department, 'Communication Arts')
        self.assertEqual(user.following, '[1, 2, 3]')

    def test_get_news_source(self):
        news_source_list = NewsCategory.query.all()
        print(NewsCategory.serialize_list(news_source_list))
        response = self.client.get('/api/v1/news-source')
        json_data = response.get_json()
        self.assertEqual(NewsCategory.serialize_list(news_source_list), json_data['news_source_list'])

    def test_get_news(self):
        # user_id = None
        response = self.client.get('/api/v1/news')
        news_list = News.query.order_by(News.date.desc()).all()
        json_data = response.get_json()
        news = News.serialize_list(news_list)
        # because the format of date is not the same, but value is same, ignore it is fine
        for item in json_data['news']:
            item.pop('date')
        for item in news:
            item.pop('date')
        self.assertEqual(news,json_data['news'])

        # user_id = user.id, has following
        response = self.client.get('/api/v1/news', headers={'token': generate_token(1)})
        news_list = News.query.filter_by(source_id=1).order_by(News.date.desc())
        json_data = response.get_json()
        news = News.serialize_list(news_list)
        # because the format of date is not the same, but value is same, ignore it is fine
        for item in json_data['news']:
            item.pop('date')
        for item in news:
            item.pop('date')
        self.assertEqual(news, json_data['news'])

        # user_id = user.id, no following
        response = self.client.get('/api/v1/news', headers={'token': generate_token(2)})
        news_list = News.query.order_by(News.date.desc()).all()
        json_data = response.get_json()
        news = News.serialize_list(news_list)
        # because the format of date is not the same, but value is same, ignore it is fine
        for item in json_data['news']:
            item.pop('date')
        for item in news:
            item.pop('date')
        self.assertEqual(news, json_data['news'])

    def test_get_news_by_source(self):
        response = self.client.get('/api/v1/news/1')
        news_list = News.query.filter_by(source_id=1).order_by(News.date.desc())
        news = News.serialize_list(news_list)
        json_data = response.get_json()
        for item in news:
            item.pop('date')
        for item in json_data['news']:
            item.pop('date')
        self.assertEqual(news, json_data['news'])

# ******************* test commands.py ******************* #
    def test_

if __name__ == '__main__':
    unittest.main()