"""Enable third party extensions."""

from celery import Celery
from flask_migrate import Migrate  # type: ignore
from flask_socketio import SocketIO  # type: ignore
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect  # type: ignore

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
celery = Celery(__name__)
csrf = CSRFProtect()
