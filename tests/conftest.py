"""A series of fixtures that are shared among all tests."""

import logging
import os
import uuid
from typing import Any, Generator
from unittest.mock import Mock

import pytest
from flask import Flask
from flask_socketio import SocketIOTestClient  # type: ignore
from flask_sqlalchemy import SQLAlchemy
from pytest_mock.plugin import MockerFixture
from webtest import TestApp  # type: ignore

os.environ["MATL_ONLINE_ENV"] = "test"

from matl_online.app import create_app  # noqa: E402
from matl_online.database import db as _db  # noqa: E402
from matl_online.extensions import socketio  # noqa: E402
from matl_online.settings import TestConfig  # noqa: E402
from matl_online.tasks import OutputHandler  # noqa: E402


@pytest.fixture(scope="function")
def testapp(app: Flask) -> TestApp:
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture(scope="function")
def socketio_client(app: Flask) -> SocketIOTestClient:
    """Fake socketio client."""
    return SocketIOTestClient(app, socketio)


@pytest.fixture(scope="function")
def app() -> Generator[Flask, None, None]:
    """Flask app instance."""
    app_instance = create_app(TestConfig)
    context = app_instance.test_request_context()
    context.push()  # type: ignore[attr-defined]

    yield app_instance

    context.pop()  # type: ignore[attr-defined]


@pytest.fixture(scope="function")
def logger() -> Generator[logging.Logger, None, None]:
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
def octave_mock(
    mocker: MockerFixture,
    logger: logging.Logger,
) -> Mock:
    """Mock version of OctaveEngine to monitor calls to octave."""
    octave = mocker.patch("matl_online.tasks.octave")
    octave.evals = list()

    def octave_eval(*args: Any, **kwargs: Any) -> None:
        octave.evals.append(*args)

    octave.eval = octave_eval
    octave.logger = logger
    return octave


@pytest.fixture(scope="function")
def db(app: Flask) -> Generator[SQLAlchemy, None, None]:
    """Database instance."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close the database connection
    _db.session.close()
    _db.drop_all()
