""" User model tests """

# run these tests like:
# export ENV=testing
# python -m unittest discover -s tests
# OR:
# python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User

from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """ Test user model """

    def setUp(self):
        """ Create test client, add sample data """

        db.drop_all()
        db.create_all()

        self.user = User.signup('testuser', 'testuser@example.com', 'Password8784$$')
        
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

    def test_user_model(self):
        """ Does basic model, non signup or auth"""

        u = User(username='testacct', email='test@test.com', password='Password8784$$')
        
        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.username, 'testacct')

    def test_valid_signup(self):
        u1 = User.signup('testuser2023', 'testu@test.com', 'Password8784$$')
        u1_id = 999
        u1.id = u1_id
        db.session.commit()

        u_test = User.query.get(u1_id)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "testuser2023")
        self.assertEqual(u_test.email, "testu@test.com")
        self.assertNotEqual(u_test.password, "Password8784$$")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        with self.assertRaises(ValueError) as context:
            invalid = User.signup(None, "test44@test.com", "Password8784$$")
            uid = 12345
            invalid.id = uid
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()  # Rollback the transaction in case of error
                assert "Username and email must not be empty" in str(context.exception)

    def test_invalid_email_signup(self):
        with self.assertRaises(ValueError) as context:
            invalid = User.signup("test22", None, "Password8784$$")
            uid = 123789
            invalid.id = uid
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()  # Rollback the transaction in case of error
                assert "Username and email must not be empty" in str(context.exception)

    # Unsure if this is working..
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@test.com", "")
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@test.com", None)