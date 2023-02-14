"""Enable third party extensions."""

import rollbar  # type: ignore[import]
from celery import Celery
from flask_migrate import Migrate  # type: ignore[import]
from flask_socketio import SocketIO  # type: ignore[import]
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect  # type: ignore[import]

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
celery = Celery(__name__)
csrf = CSRFProtect()

__all__ = ["rollbar", "db", "migrate", "socketio", "celery", "csrf"]
