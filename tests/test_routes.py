# Testing via Terminal
# export ENV=testing
# python -m unittest discover -s tests

import os
import unittest
from app import app, db, User

class BaseTestCase(unittest.TestCase):

    def create_app(self):
        app.config['ENV'] = 'testing'
        #app.config['TESTING'] = True
        #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory SQLite database for testing
        return app

    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


class AuthTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()  # Call setUp on the base test case to set up the app and the database
        self.user = User.signup('testuser', 'testuser@example.com', 'password')  # Create a test user
        db.session.commit()
        self.client.post('/login', data=dict(
            username='testuser',
            password='password'
        ), follow_redirects=True)

    def tearDown(self):
        User.query.delete()  # Delete all users
        db.session.commit()
        super().tearDown()  # Call tearDown on the base test case to tear down the app and the database

    def test_login(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'Successfully logged out.', response.data)


class NoAuthTestCase(BaseTestCase):
    """For routes that do not require authentication"""

    def test_signup(self):
        response = self.client.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome newuser!', response.data)  # Check if the flash message is present in the response
        self.assertRedirects(response, '/')  # Check if the response is redirected to the home page

    def test_login_non_existent_user(self):
        response = self.client.post('/login', data={
            'username': 'nonexistentuser',
            'password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid credentials.', response.data)
