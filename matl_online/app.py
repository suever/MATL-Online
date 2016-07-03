# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask

from matl_online import public
from matl_online.assets import assets
from matl_online.extensions import db, migrate, socketio, celery
from matl_online.settings import ProdConfig


def create_app(config_object=ProdConfig):
    """
    An application factory, as explained here:
    http://flask.pocoo.org/docs/patterns/appfactories/.
    :param config_object: The configuration object to use.
    """
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
    socketio.init_app(app, message_queue='redis://')
    celery.conf.update(app.config)


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    return None
