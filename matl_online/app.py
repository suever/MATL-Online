"""The app module, containing the app factory function."""
from typing import Optional, Type

from flask import Flask

from matl_online import public
from matl_online.assets import assets
from matl_online.commands import register_commands
from matl_online.extensions import celery, csrf, db, migrate, socketio
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
        cors_allowed_origins=app.config.get("CORS_ALLOWED_ORIGINS"),
    )

    celery.conf.update(get_celery_configuration(app.config))
    csrf.init_app(app)


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    return None
