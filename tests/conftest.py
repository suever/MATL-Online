import logging
import pytest
import uuid

from webtest import TestApp

from matl_online.app import create_app
from matl_online.database import db as _db
from matl_online.extensions import socketio
from matl_online.settings import TestConfig
from matl_online.tasks import OutputHandler


@pytest.fixture(scope='function')
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.yield_fixture(scope='function')
def socketclient(app):
    socketio.init_app(app)
    yield socketio.test_client(app)


@pytest.yield_fixture(scope='function')
def app():
    _app = create_app(TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.yield_fixture(scope='function')
def logger():
    # Create a new random log
    logger = logging.getLogger(str(uuid.uuid4()))
    logger.setLevel(logging.INFO)

    yield logger

    for handler in logger.handlers:
        if isinstance(handler, OutputHandler):
            handler.clear()

    logger.handlers = []


@pytest.fixture
def moctave(mocker, logger):
    moctave = mocker.patch('oct2py.octave')
    moctave.evals = list()

    def moctave_eval(*args, **kwargs):
        moctave.evals.append(*args)

    moctave.eval = moctave_eval
    moctave.logger = logger
    return moctave


@pytest.yield_fixture(scope='function')
def db(app):
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close the database connection
    _db.session.close()
    _db.drop_all()
