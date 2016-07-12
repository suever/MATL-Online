"""Application configuration."""
import os
import uuid


class Config(object):
    """Base configuration."""

    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERYD_TASK_SOFT_TIME_LIMIT = 30
    CELERYD_TASK_TIME_LIMIT = 60

    IMGUR_CLIENT_ID = os.environ.get('MATL_ONLINE_IMGUR_CLIENT_ID')

    SECRET_KEY = str(uuid.uuid4())
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_NAME = 'database.db'
    DB_PATH = os.path.join(PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(DB_PATH)

    # Directories
    MATL_FOLDER = os.path.join(PROJECT_ROOT, 'MATL')
    MATL_WRAP_DIR = os.path.join(MATL_FOLDER, 'wrappers')

    # Github / Repo settings
    MATL_REPO = 'lmendo/MATL'
    GITHUB_API = 'https://api.github.com'
    GITHUB_HOOK_SECRET = os.environ.get('MATL_ONLINE_GITHUB_HOOK_SECRET')


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False
    ASSETS_DEBUG = False


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    ASSETS_DEBUG = True


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
