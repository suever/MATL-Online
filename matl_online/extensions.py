"""Enable third party extensions."""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_wtf import CsrfProtect

from celery import Celery
from matl_online.settings import Config


db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)
csrf = CsrfProtect()
