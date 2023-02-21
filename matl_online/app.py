"""The app module, containing the app factory function."""
from typing import Optional, Type

from flask import Flask, got_request_exception
from rollbar.contrib.flask import report_exception  # type: ignore[import]

from matl_online import public
from matl_online.assets import assets
from matl_online.commands import register_commands
from matl_online.extensions import celery, csrf, db, metrics, migrate, rollbar, socketio
from matl_online.settings import Config, get_celery_configuration, get_config


def create_app(config_object: Optional[Type[Config]] = None) -> Flask:
    """Application factory for creating flask apps."""
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    return app


def register_extensions(app: Flask) -> None:
    """Register Flask extensions."""
    assets.init_app(app)
    db.init_app(app)  # type: ignore[no-untyped-call]
    migrate.init_app(app, db)

    # Make sure that the client manager isn't remembered
    socketio.server_options.pop("client_manager", None)
    socketio.init_app(
        app,
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),
        cors_allowed_origins="*",
    )

    register_rollbar(app)

    celery.conf.update(get_celery_configuration(app.config))
    csrf.init_app(app)

    metrics.init_app(app)
    metrics.info("app_info", "Application info", version=app.config.get("APP_VERSION"))


def register_rollbar(app: Flask) -> None:
    rollbar.init(
        app.config.get("ROLLBAR_SERVER_SIDE_TOKEN"),
        environment=app.config.get("ROLLBAR_ENV"),
        root=app.config.get("PROJECT_ROOT"),
        allow_logging_basic_config=False,
        code_version=app.config.get("APP_VERSION"),
    )

    got_request_exception.connect(report_exception, app)


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    return None


__all__ = [
    "celery",
    "create_app",
    "metrics",
]
