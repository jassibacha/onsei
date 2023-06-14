import os
import unittest
from app import app, db, User

class BaseTestCase(unittest.TestCase):

    def create_app(self):
        app.config['ENV'] = 'testing'
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory SQLite database for testing
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


class NoAuthTestCase(BaseTestCase):
    """For routes that do not require authentication"""

    pass
