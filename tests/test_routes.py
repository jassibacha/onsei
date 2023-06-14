# Testing via Terminal
# export ENV=testing
# python -m unittest discover -s tests

import os
import unittest
from unittest import TestCase
from models import db, User
from app import app
from datetime import datetime


class RoutesTestCase(TestCase):

    def create_app(self):
        app.config['ENV'] = 'testing'
        #app.config['SECRET_KEY'] = 'notsosecret'
        #app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///onsei-test'  # Use an in-memory SQLite database for testing
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.user = User.signup('testuser', 'testuser@example.com', 'Password8784$$')
        self.user.anilist_username = 'hopesix'
        self.user.anilist_profile_accessible = True
        self.user.anime_list = {
            21366: {"status": "COMPLETED", "score": 9},
            98478: {"status": "COMPLETED", "score": 10},
            9624: {"status": "COMPLETED", "score": 7},
            100526: {"status": "COMPLETED", "score": 5},
            21711: {"status": "COMPLETED", "score": 8},
            98251: {"status": "COMPLETED", "score": 7},
            21058: {"status": "COMPLETED", "score": 7},
            20613: {"status": "COMPLETED", "score": 7},
            20770: {"status": "COMPLETED", "score": 8},
            47: {"status": "COMPLETED", "score": 7},
            100645: {"status": "COMPLETED", "score": 6}
        }
        self.user.anime_list_updated_at = datetime.utcnow()
        db.session.commit()

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        User.query.delete()
        db.session.commit()
        db.drop_all()
        self.app_context.pop()
    
    def test_index(self):
        """ Does index route work """
        with self.client as c:
            resp = c.get('/', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Onsei', str(resp.data))

    def test_signup(self):
        """ Does signup work """

        with self.client as c: 
            resp = c.get('/signup')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sign Up', str(resp.data))

        with self.client as c: 
            form_data = {
                'username': 'testuser1', 
                'email': 'testuser1@test.com', 
                'password': 'TestPassword8723@(**',
                'confirm_password': 'TestPassword8723@(**'}
            resp = c.post('/signup', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Signup Successful', str(resp.data))

    def test_failed_signup_weakpass(self):
        """ Does signup work """

        with self.client as c: 
            resp = c.get('/signup')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sign Up', str(resp.data))

        with self.client as c: 
            form_data = {
                'username': 'testuser1', 
                'email': 'testuser1@test.com', 
                'password': 'weakpass',
                'confirm_password': 'weakpass'}
            resp = c.post('/signup', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Password must include at least one of each', str(resp.data))

    def test_login(self):
        """ Ensures login works """

        with self.client as c:
            resp = c.get('/login')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome', str(resp.data))

        with self.client as c: 
            form_data = {'username': 'testuser', 'password': 'Password8784$$'}
            resp = c.post('/login', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('successful', str(resp.data))


# class AuthTestCase(BaseTestCase):

#     def setUp(self):
#         # Call setUp on the base test case to set up the app and the database
#         super().setUp() 
#         # Create a test user
#         self.user = User.signup('testuser', 'testuser@example.com', 'password')
#         self.user.anilist_username = 'hopesix'
#         self.user.anilist_profile_accessible = True
#         self.user.anime_list = {
#             21366: {"status": "COMPLETED", "score": 9},
#             98478: {"status": "COMPLETED", "score": 10},
#             9624: {"status": "COMPLETED", "score": 7},
#             100526: {"status": "COMPLETED", "score": 5},
#             21711: {"status": "COMPLETED", "score": 8},
#             98251: {"status": "COMPLETED", "score": 7},
#             21058: {"status": "COMPLETED", "score": 7},
#             20613: {"status": "COMPLETED", "score": 7},
#             20770: {"status": "COMPLETED", "score": 8},
#             47: {"status": "COMPLETED", "score": 7},
#             100645: {"status": "COMPLETED", "score": 6}
#         }
#         self.user.anime_list_updated_at = datetime.utcnow
#         db.session.commit()

#     def tearDown(self):
#         User.query.delete()  # Delete all users
#         db.session.commit()
#         super().tearDown()  # Call tearDown on the base test case to tear down the app and the database

#     # def test_login(self):
#     #     response = self.client.get('/login')
#     #     self.assertEqual(response.status_code, 200)

#     # def test_logout(self):
#     #     response = self.client.get('/logout', follow_redirects=True)
#     #     self.assertIn(b'Successfully logged out.', response.data)


# class NoAuthTestCase(BaseTestCase):
#     """For routes that do not require authentication"""

#     def test_index(self):
#         """ Does index route work """

#         with self.client as c:
#             resp = c.get('/', follow_redirects=True)

#             self.assertEqual(resp.status_code, 200)
#             self.assertIn('Onsei', str(resp.data))


