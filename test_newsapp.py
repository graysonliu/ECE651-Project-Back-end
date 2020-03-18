import unittest
import time
import os
from datetime import datetime
from sqlalchemy import or_
import getpass
from unittest.mock import patch

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
            FLASK_ENV='development',
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
        )
        db.create_all()  # create database and all tables

        # insert two users
        user1 = User(
            name='test', username='test_user', gender=1,
            faculty='Engineering', department='Electrical and Computer Engineering',
            admin=False, following='1, 2'
        )
        user1.set_password('123')

        user2 = User(
            name='test', username='test_user2', gender=1,
            faculty='Engineering', department='Electrical and Computer Engineering',
            admin=False
        )
        user2.set_password('123')

        admin = User(username='test_admin', admin=True)
        admin.set_password('admin')

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

        db.session.add_all([user1, user2, admin, category1, category2, source1, source2, news1, news2])
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

# ******************* test errors.py ******************* #
    def test_error_404(self):
        response = self.client.post('/api/vi/user')
        json_data = response.get_json()
        self.assertEqual(None, json_data['error_code'])
        self.assertEqual('404 Not Found.', json_data['description'])

# ******************* test auth.py ******************* #
    def test_verify_token(self):
        # token is valid
        token = generate_token(1)
        self.assertEqual(User.query.get(1), verify_token(token))
        # token is 'admin'
        token = 'admin'
        self.assertEqual('admin', verify_token(token))
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

# ******************* test user in routes.py ******************* #
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
        self.assertEqual(User.query.get(4), verify_token(json_data['token']))

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

        # hold own token to access other's profile
        response = self.client.get('/api/v1/users/1', headers={'token': generate_token(2)})
        json_data = response.get_json()
        self.assertEqual(1002, json_data['error_code'])
        self.assertEqual('No permission.', json_data['description'])

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
                                           'following': '1, 2, 3'})
        user = User.query.get(1)
        self.assertEqual(user.faculty, 'Arts')
        self.assertEqual(user.department, 'Communication Arts')
        self.assertEqual(user.following, '1, 2, 3')

    def test_get_news_source(self):
        news_source_list = NewsCategory.query.all()
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
        news_list = News.query.filter(or_(News.source_id == 1, News.source_id == 2)).order_by(News.date.desc())
        json_data = response.get_json()
        news = News.serialize_list(news_list)
        # because the format of date is not the same, but value is same, ignore it is fine
        for item in json_data['news']:
            item.pop('date')
        for item in news:
            item.pop('date')
        self.assertEqual(json_data['news'], news)

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

# ******************* test admin in routes.py ******************* #
    def test_development_env(self):
        self.assertEqual('development', os.environ.get('FLASK_ENV'))

    def test_get_user_list(self):
        # as admin, success
        response = self.client.get('/api/v1/users', headers={'token': 'admin'})
        json_data = response.get_json()
        user_list = User.query.all()
        users = User.serialize_list(user_list)
        self.assertEqual(users, json_data['user_list'])

        # not as admin, fail
        response = self.client.get('/api/v1/users', headers={'token': generate_token(1)})
        json_data = response.get_json()
        user_list = User.query.all()
        users = User.serialize_list(user_list)
        self.assertEqual(1002, json_data['error_code'])
        self.assertEqual('No permission.', json_data['description'])

    def test_admin_get_user_info(self):
        # hold own token to access own profile
        user = User.query.get(3)
        response = self.client.get('/api/v1/users/3', headers={'token': 'admin'})
        json_data = response.get_json()
        self.assertEqual(user.serialize(), json_data)

        # hold own token to access other's profile
        user = User.query.get(1)
        response = self.client.get('/api/v1/users/1', headers={'token': 'admin'})
        json_data = response.get_json()
        self.assertEqual(user.serialize(), json_data)

    def test_admin_update_user_info(self):
        # change other users info
        # change password
        # old password is wrong
        response = self.client.patch('/api/v1/users/1', headers={'token': 'admin'},
                                     json={'old_password': '456', 'new_password': '222'})
        json_data = response.get_json()
        self.assertEqual(1004, json_data['error_code'])
        self.assertEqual('Authentication failure.', json_data['description'])
        # new password is None
        response = self.client.patch('/api/v1/users/1', headers={'token': 'admin'},
                                     json={'old_password': '123'})
        json_data = response.get_json()
        self.assertEqual(1006, json_data['error_code'])
        # change password success
        response = self.client.patch('/api/v1/users/1', headers={'token': 'admin'},
                                     json={'old_password': '123', 'new_password': '222'})
        user = User.query.get(1)
        self.assertTrue(user.verify_password('222'))

        # change username
        # new username is existed
        response = self.client.patch('/api/v1/users/1', headers={'token': 'admin'},
                                     json={'username': 'test_user2'})
        json_data = response.get_json()
        self.assertEqual(1005, json_data['error_code'])
        # change username success
        response = self.client.patch('/api/v1/users/1', headers={'token': 'admin'},
                                     json={'username': 'new_username'})
        user = User.query.get(1)
        self.assertEqual(user.username, 'new_username')

        # change ['name', 'gender', 'faculty', 'department', 'following']
        response = self.client.patch('/api/v1/users/1', headers={'token': 'admin'},
                                     json={'gender': 0, 'faculty': 'Arts', 'department': 'Communication Arts',
                                           'following': '1, 2, 3'})
        user = User.query.get(1)
        self.assertEqual(user.faculty, 'Arts')
        self.assertEqual(user.department, 'Communication Arts')
        self.assertEqual(user.following, '1, 2, 3')

    def test_admin_update_info(self):
        # change admin its own info
        # change password
        # old password is wrong
        response = self.client.patch('/api/v1/users/3', headers={'token': 'admin'},
                                     json={'old_password': '456', 'new_password': '222'})
        json_data = response.get_json()
        self.assertEqual(1004, json_data['error_code'])
        self.assertEqual('Authentication failure.', json_data['description'])
        # new password is None
        response = self.client.patch('/api/v1/users/3', headers={'token': 'admin'},
                                     json={'old_password': 'admin'})
        json_data = response.get_json()
        self.assertEqual(1006, json_data['error_code'])
        # change password success
        response = self.client.patch('/api/v1/users/3', headers={'token': 'admin'},
                                     json={'old_password': 'admin', 'new_password': '222'})
        user = User.query.get(3)
        self.assertTrue(user.verify_password('222'))

        # change username
        # new username is existed
        response = self.client.patch('/api/v1/users/3', headers={'token': 'admin'},
                                     json={'username': 'test_user2'})
        json_data = response.get_json()
        self.assertEqual(1005, json_data['error_code'])
        # change username success
        response = self.client.patch('/api/v1/users/3', headers={'token': 'admin'},
                                     json={'username': 'new_admin'})
        user = User.query.get(3)
        self.assertEqual(user.username, 'new_admin')

        # change ['name', 'gender', 'faculty', 'department', 'following']
        response = self.client.patch('/api/v1/users/3', headers={'token': 'admin'},
                                     json={'gender': 0, 'faculty': 'Arts', 'department': 'Communication Arts',
                                           'following': '1, 2, 3'})
        user = User.query.get(3)
        self.assertEqual(user.faculty, 'Arts')
        self.assertEqual(user.department, 'Communication Arts')
        self.assertEqual(user.following, '1, 2, 3')

    def test_admin_get_news(self):
        # user = admin
        response = self.client.get('/api/v1/news', headers={'token': 'admin'})
        news_list = News.query.order_by(News.date.desc()).all()
        json_data = response.get_json()
        news = News.serialize_list(news_list)
        # because the format of date is not the same, but value is same, ignore it is fine
        for item in json_data['news']:
            item.pop('date')
        for item in news:
            item.pop('date')
        self.assertEqual(news, json_data['news'])

# ******************* test commands.py ******************* #
    def test_init_db(self):
        result = self.runner.invoke(init_db)
        self.assertEqual(User.query.all(), [])
        self.assertEqual(NewsCategory.query.all(), [])
        self.assertEqual(NewsSource.query.all(), [])
        self.assertEqual(News.query.all(), [])
        self.assertEqual('Finish initializing database.\n', result.output)

    def test_create_admin(self):
        # create fail, username is existed
        result = self.runner.invoke(create_admin, args=['--username', 'test_admin', '--password', 'root'])
        self.assertEqual('Admin "test_admin" already exists.\n', result.output)

        # create success
        result = self.runner.invoke(create_admin, args=['--username', 'new_admin', '--password', 'root'])
        self.assertEqual('Done.\n', result.output)
        user = User.query.filter_by(username='new_admin').first()
        user.set_password('root')
        self.assertEqual(user.username, 'new_admin')
        self.assertTrue(user.verify_password('root'))

    @patch('getpass.getpass', return_value='new_password')
    def test_update_admin(self, input):
        # update fail, username=None
        result = self.runner.invoke(update_admin, args=['--username', '', '--password', 'admin'])
        self.assertEqual('Wrong username or password of admin.\n', result.output)

        # update fail, username is not admin
        result = self.runner.invoke(update_admin, args=['--username', 'test1', '--password', '123'])
        self.assertEqual('Wrong username or password of admin.\n', result.output)

        # update success
        result = self.runner.invoke(update_admin, args=['--username', 'test_admin', '--password', 'admin'])
        self.assertEqual('Done.\n', result.output)

    # success to delete
    @patch('builtins.input', return_value='y')
    def test_delete_admin(self, input):
        result = self.runner.invoke(delete_admin, args=['--username', 'test_admin', '--password', 'admin'])
        print(result.output)
        self.assertEqual('Done.\n', result.output)

    # in process of delete
    def test_delete_admin2(self):
        result = self.runner.invoke(delete_admin, args=['--username', 'test_admin', '--password', 'admin'])
        expect = 'Are you sure you want to delete admin account test_admin? (y/n) \nAborted!\n'
        self.assertEqual(expect, result.output)

    # fail to delete
    @patch('builtins.input', return_value='n')
    def test_delete_admin3(self, input):
        result = self.runner.invoke(delete_admin, args=['--username', 'test_admin', '--password', 'admin'])
        expect = 'Aborted!\n'
        self.assertEqual(expect, result.output)

    def test_init_source(self):
        result = self.runner.invoke(init_sources)
        category = NewsCategory.query.get(1)
        self.assertEqual(category.name, 'University')

        source = NewsSource.query.get(1)
        self.assertEqual(source.url, 'https://uwaterloo.ca/news/news')
        self.assertEqual(source.name, 'Waterloo News')
        self.assertEqual(source.uw_style, True)
        self.assertEqual(source.category_id, 1)


if __name__ == '__main__':
    unittest.main()