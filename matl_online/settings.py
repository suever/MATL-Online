"""Application configuration."""
import os
import pathlib
import uuid
from typing import Any, Dict, List, Optional, Type

from flask.config import Config as FlaskConfig


def _get_cors_allowed_origins() -> List[str]:
    provided_value = os.getenv("CORS_ALLOWED_ORIGINS")

    if provided_value is None or provided_value == "":
        return []

    return provided_value.split(";")


class Config(object):
    """Base configuration."""

    ENV: str = "NONE"

    # Custom timeout for celery process initialization
    CELERY_PROCESS_INIT_TIMEOUT = 10

    IMGUR_CLIENT_ID = os.environ.get("MATL_ONLINE_IMGUR_CLIENT_ID")

    SECRET_KEY = str(uuid.uuid4())
    APP_DIR = pathlib.Path(os.path.dirname(__file__)).absolute()  # This directory
    PROJECT_ROOT = APP_DIR.parent

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_NAME = "database.db"
    DB_PATH = PROJECT_ROOT.joinpath(DB_NAME)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", f"sqlite:///{DB_PATH.as_posix()}"
    )

    # Directories
    MATL_FOLDER = PROJECT_ROOT.joinpath("MATL")
    MATL_WRAP_DIR = MATL_FOLDER.joinpath("wrappers")

    # Octave settings
    OCTAVE_CLI_OPTIONS = "--norc --no-history"
    OCTAVE_EXECUTABLE = "octave-cli"
    OCTAVERC = MATL_WRAP_DIR.joinpath(".octaverc")

    # GitHub / Repo settings
    MATL_REPO = "lmendo/MATL"
    GITHUB_API = "https://api.github.com"
    GITHUB_HOOK_SECRET = os.environ.get("MATL_ONLINE_GITHUB_HOOK_SECRET")

    # Don't use Google Analytics unless we are on production
    GOOGLE_ANALYTICS_UNIVERSAL_ID: Optional[str] = None

    SOCKETIO_MESSAGE_QUEUE = os.environ.get("SOCKETIO_MESSAGE_QUEUE")

    # Rollbar
    ROLLBAR_SERVER_SIDE_TOKEN = os.environ.get("MATL_ONLINE_ROLLBAR_SERVER_SIDE_TOKEN")
    ROLLBAR_CLIENT_SIDE_TOKEN = os.environ.get("MATL_ONLINE_ROLLBAR_CLIENT_SIDE_TOKEN")

    # CORS Configuration for Flask SocketIO
    CORS_ALLOWED_ORIGINS: List[str] = _get_cors_allowed_origins()


class ProdConfig(Config):
    """Production configuration."""

    ENV = "prod"
    DEBUG = False
    ASSETS_DEBUG = False

    GOOGLE_ANALYTICS_UNIVERSAL_ID = os.environ.get("GOOGLE_ANALYTICS_UNIVERSAL_ID")

    ROLLBAR_ENV = "production"


class DevConfig(Config):
    """Development configuration."""

    ENV = "dev"
    DEBUG = True
    ASSETS_DEBUG = True

    ROLLBAR_ENV = "development"


class TestConfig(Config):
    """Test configuration."""

    ENV = "test"
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"

    IMGUR_CLIENT_ID = "imgur_test"

    WTF_CSRF_ENABLED = False

    PRESERVE_CONTEXT_ON_EXCEPTION = False

    # Create a bogus GA Universal ID for testing
    GOOGLE_ANALYTICS_UNIVERSAL_ID = "nonsense"

    ROLLBAR_ENV = "testing"


def get_config() -> Type[Config]:
    """Retrieve the current active configuration based on env variables."""
    env = os.environ.get("MATL_ONLINE_ENV", "dev")

    return {"prod": ProdConfig, "dev": DevConfig, "test": TestConfig}[env.lower()]


config = get_config()


def get_celery_configuration(configuration: FlaskConfig) -> Dict[str, Any]:
    return {
        "broker_url": os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "result_backend": os.environ.get(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
        ),
        "task_soft_time_limit": 30,
        "task_time_limit": 60,
        # Ensure that celery tasks are executed locally when in a test environment
        "task_always_eager": configuration.get("ENV") == "test",
        # Use pickling for serialization to allow first-class objects rather than dicts.
        # The source is also trusted therefore it should be secure enough
        "accept_content": ["application/json", "application/x-python-serialize"],
        "task_serializer": "pickle",
        "result_serializer": "pickle",
    }
