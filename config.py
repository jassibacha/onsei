""" Config class setup """
import os

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    ANILIST_CLIENT_ID = os.environ.get('ANILIST_CLIENT_ID')
    ANILIST_CLIENT_SECRET = os.environ.get('ANILIST_CLIENT_SECRET')
    # ANILIST_API_URL = 'https://graphql.anilist.co'
    # ANILIST_API_HEADERS = {'Content-Type': 'application/json'}
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    DEBUG = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class ProductionConfig(Config):
    # WTF_CSRF_ENABLED = False
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class TestingConfig(Config):
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql:///onsei-test'