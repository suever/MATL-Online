"""Enable third party extensions."""

import rollbar  # type: ignore[import]
from celery import Celery
from flask_migrate import Migrate  # type: ignore[import]
from flask_socketio import SocketIO  # type: ignore[import]
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect  # type: ignore[import]
from prometheus_flask_exporter import PrometheusMetrics  # type: ignore[import]

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
celery = Celery(__name__)
csrf = CSRFProtect()
metrics = PrometheusMetrics.for_app_factory()

__all__ = [
    "celery",
    "csrf",
    "db",
    "metrics",
    "migrate",
    "rollbar",
    "socketio",
]
