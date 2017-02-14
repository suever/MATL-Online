"""Application configuration."""
import os
import uuid


class Config(object):
    """Base configuration."""

    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERYD_TASK_SOFT_TIME_LIMIT = 30
    CELERYD_TASK_TIME_LIMIT = 60

    # Custom timeout for celery process initialization
    CELERY_PROCESS_INIT_TIMEOUT = 10

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

    # Octave settings
    OCTAVE_EXECUTABLE = 'octave-cli --norc --no-history'

    # Github / Repo settings
    MATL_REPO = 'lmendo/MATL'
    GITHUB_API = 'https://api.github.com'
    GITHUB_HOOK_SECRET = os.environ.get('MATL_ONLINE_GITHUB_HOOK_SECRET')

    # MATLAB Online Documentation links
    MATLAB_DOC_LINKS = [
        'http://www.mathworks.com/help/matlab/functionlist.html',
        'http://www.mathworks.com/help/images/functionlist.html',
        'http://www.mathworks.com/help/stats/functionlist.html',
        'http://www.mathworks.com/help/symbolic/functionlist.html']

    # Flower configuration
    FLOWER_OAUTH2_KEY = os.environ.get('MATL_ONLINE_GITHUB_CLIENT_ID')
    FLOWER_OAUTH2_SECRET = os.environ.get('MATL_ONLINE_GITHUB_CLIENT_SECRET')
    FLOWER_OAUTH2_REDIRECT_URI = 'https://matl.suever.net/admin/login'
    FLOWER_BROKER_API = CELERY_BROKER_URL
    FLOWER_URL_PREFIX = 'admin'
    FLOWER_PERSISTENT = True
    FLOWER_AUTH_PROVIDER = 'flower.views.auth.GithubLoginHandler'
    FLOWER_COOKIE_SECRET = SECRET_KEY
    FLOWER_AUTH = os.environ.get('MATL_ONLINE_FLOWER_AUTH')

    # Don't use google analytics unless we are on production
    GOOGLE_ANALYTICS_UNIVERSAL_ID = None

    SOCKETIO_MESSAGE_QUEUE = None


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False
    ASSETS_DEBUG = False

    GOOGLE_ANALYTICS_UNIVERSAL_ID = os.environ.get('GOOGLE_ANALYTICS_UNIVERSAL_ID')

    SOCKETIO_MESSAGE_QUEUE = 'redis://'


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    ASSETS_DEBUG = True

    SOCKETIO_MESSAGE_QUEUE = 'redis://'


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

    IMGUR_CLIENT_ID = 'imgur_test'

    WTF_CSRF_ENABLED = False

    # Ensure that celery tasks are executed locally
    CELERY_ALWAYS_EAGER = True

    PRESERVE_CONTEXT_ON_EXCEPTION = False

    # Create a bogus GA Universal ID for testing
    GOOGLE_ANALYTICS_UNIVERSAL_ID = 'nonsense'
