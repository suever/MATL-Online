"""A series of fixtures that are shared among all tests."""

import logging
import os
import uuid

import pytest
from flask_socketio import SocketIOTestClient
from webtest import TestApp

os.environ["MATL_ONLINE_ENV"] = "test"

from matl_online.app import create_app  # noqa: E402
from matl_online.database import db as _db  # noqa: E402
from matl_online.extensions import socketio  # noqa: E402
from matl_online.settings import TestConfig  # noqa: E402
from matl_online.tasks import OutputHandler  # noqa: E402


@pytest.fixture(scope="function")
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture(scope="function")
def socketio_client(app):
    """Fake socketio client."""
    yield SocketIOTestClient(app, socketio)


@pytest.fixture(scope="function")
def app():
    """Flask app instance."""
    _app = create_app(TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope="function")
def logger():
    """Logger which can be used to monitor logging calls."""
    # Create a new random log
    logger = logging.getLogger(str(uuid.uuid4()))
    logger.setLevel(logging.INFO)

    yield logger

    for handler in logger.handlers:
        # In the special case where an OutputHandler is registered, we want
        # to clear out the message queue
        if isinstance(handler, OutputHandler):
            handler.clear()

    logger.handlers = []


@pytest.fixture
def octave_mock(mocker, logger):
    """Mock version of OctaveEngine to monitor calls to octave."""
    octave = mocker.patch("matl_online.tasks.octave")
    octave.evals = list()

    def octave_eval(*args, **kwargs):
        octave.evals.append(*args)

    octave.eval = octave_eval
    octave.logger = logger
    return octave


@pytest.fixture(scope="function")
def db(app):
    """Database instance."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close the database connection
    _db.session.close()
    _db.drop_all()
