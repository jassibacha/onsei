"""SQLAlchemy models for Onsei"""

from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PickleType
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
from api_clients import is_anilist_username_accessible
from flask import current_app
import requests

bcrypt = Bcrypt()
db = SQLAlchemy()
migrate = Migrate()


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)
    migrate.init_app(app, db)


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.String(255),
        nullable=False,
    )

    anilist_username = db.Column(
        db.String(255),
        nullable=True
    )
    anilist_profile_accessible = db.Column(db.Boolean, default=False)

    anime_list = db.Column(PickleType, nullable=True)
    anime_list_updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        # Check if the username or email already exists
        existing_user = cls.query.filter(
            (cls.username == username) | (cls.email == email)
        ).first()

        if existing_user:
            raise IntegrityError("Username or email already in use", orig=None, params=None)

        # Raise ValueError if username or email is None
        if username is None or email is None:
            raise ValueError("Username and email must not be empty")

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    def update_anilist_username(self, new_username):
        """Update the AniList username and check if the profile is accessible."""
        self.anilist_username = new_username

        # Check if the AniList username is accessible
        if is_anilist_username_accessible(new_username, current_app):
            self.anilist_profile_accessible = True
        else:
            self.anilist_profile_accessible = False



