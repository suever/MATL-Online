"""Enable third party extensions."""

from celery import Celery
from celery.concurrency import asynpool
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from matl_online.settings import Config

# Change the timeout for celery process initialization
asynpool.PROC_ALIVE_TIMEOUT = Config.CELERY_PROCESS_INIT_TIMEOUT

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)
csrf = CSRFProtect()
