"""The app module, containing the app factory function."""
from flask import Flask

from matl_online import public
from matl_online.assets import assets
from matl_online.extensions import db, migrate, socketio, celery, csrf
from matl_online.settings import ProdConfig


def create_app(config_object=ProdConfig):
    """Application factory for creating flask apps."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    assets.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # Make sure that the client manager isn't remembered
    socketio.server_options.pop('client_manager', None)
    socketio.init_app(app, message_queue=app.config.get('SOCKETIO_MESSAGE_QUEUE'))

    celery.conf.update(app.config)
    csrf.init_app(app)


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    return None
