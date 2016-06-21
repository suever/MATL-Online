"""Application configuration."""
import os
import uuid


class Config(object):
    """Base configuration."""

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
    TEMP_IMAGE_DIR = os.path.join(APP_DIR, 'static', 'temp')

    # Octave settings
    OCTAVE_TIMEOUT = 60

    # Github / Repo settings
    MATL_REPO = 'lmendo/MATL'
    GITHUB_API = 'https://api.github.com'


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
