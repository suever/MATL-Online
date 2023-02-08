"""Unit tests for basic celery task functionality."""

import logging
import pathlib
from typing import Callable
from unittest.mock import Mock

import pytest
from celery.exceptions import SoftTimeLimitExceeded
from flask_socketio import Socket, SocketIOTestClient  # type: ignore[import]
from pytest_mock.plugin import MockerFixture

from matl_online.tasks import OctaveTask, matl_task

from .helpers import session_id_for_client


def prepare_folder_testcase(mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
    """Create the necessary mocks."""
    mocker.patch("matl_online.tasks.Task")

    make_directory_mock = mocker.patch("matl_online.tasks.tempfile.mkdtemp")
    make_directory_mock.return_value = tmp_path.as_posix()

    get_temporary_directory_mock = mocker.patch("matl_online.tasks.tempfile.gettempdir")
    get_temporary_directory_mock.return_value = tmp_path.as_posix()


class TestOctaveTask:
    """Series of tests for the OctaveTask class."""

    def test_octave_property(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        logger: logging.Logger,
    ) -> OctaveTask:
        """Make sure that an instance is created only when requested."""
        mocker.patch("matl_online.tasks.Task")

        logger.setLevel(logging.ERROR)
        octave_mock.logger = logger

        task = OctaveTask()

        # Make sure that there is no _octave property
        assert task._octave is None

        new_octave = task.octave

        assert task._octave == new_octave
        assert new_octave == octave_mock

        return task

    def test_octave_property_repeat(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        logger: logging.Logger,
    ) -> None:
        """Octave sessions are only created once per task."""
        task = self.test_octave_property(mocker, octave_mock, logger)

        # Get the property again and make sure we don't create a new
        # instance
        assert task.octave == octave_mock

    def test_folder_no_session(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        tmp_path: pathlib.Path,
    ) -> None:
        """Test the dynamic folder property when there is no session."""
        prepare_folder_testcase(mocker, tmp_path)

        task = OctaveTask()

        assert tmp_path.is_dir()
        assert task.folder == tmp_path
        assert tmp_path.is_dir()

    def test_folder_with_session(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        tmp_path: pathlib.Path,
    ) -> None:
        """Test the folder property when we DO have a session."""
        prepare_folder_testcase(mocker, tmp_path)

        task = OctaveTask()
        session_id = "123456"
        task.session_id = session_id

        output_directory = tmp_path.joinpath(session_id)

        assert not output_directory.is_dir()
        assert task.folder == output_directory
        assert output_directory.is_dir()

    def test_on_term(self, mocker: MockerFixture, octave_mock: Mock) -> None:
        """Ensure cleanup is performed as expected when a task is terminated."""
        initialize = mocker.patch("matl_online.tasks._initialize_process")

        task = OctaveTask()

        # Hopefully we kill the current thing, restart octave, and
        # initialize
        task.on_term()

        methods = [m[0] for m in octave_mock.method_calls]

        assert "restart" in methods
        assert initialize.call_count == 1


def _get_socket_for_client(client: SocketIOTestClient) -> Callable[[], Socket]:
    return lambda: client.socketio


class TestMATLTask:
    """Tests for the MATLTask subclass of OctaveTask."""

    def test_normal(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        socketio_client: SocketIOTestClient,
    ) -> None:
        """Test that messages are received as expected in normal case."""
        # Clear out the socket client's messages so far
        socketio_client.get_received()

        # Overload the use of the message_queue by simply mocking the
        # socket instance in tasks.py
        mocker.patch(
            "matl_online.tasks.socket",
            new_callable=_get_socket_for_client(socketio_client),
        )

        matl_task(
            "-ro",
            "1D",
            "",
            "20.0.0",
            session_id_for_client(socketio_client),
        )

        received = socketio_client.get_received()
        assert received[-1]["args"][0] == {"message": "", "success": True}

    def test_keyboard_interrupt(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        socketio_client: SocketIOTestClient,
    ) -> None:
        """Ensure proper handling of keyboard interrupt events."""
        socketio_client.get_received()

        mocker.patch(
            "matl_online.tasks.socket",
            new_callable=_get_socket_for_client(socketio_client),
        )

        ev = mocker.patch("matl_online.tasks.matl_task.octave.eval")
        ev.side_effect = KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            matl_task(
                "-ro",
                "1D",
                "",
                "20.0.0",
                session_id_for_client(socketio_client),
            )

        received = socketio_client.get_received()

        payload = received[0]["args"][0]

        assert payload.get("session") == session_id_for_client(socketio_client)
        assert payload["data"][0]["type"] == "stderr"
        assert payload["data"][0]["value"] == "Job cancelled"

        # Ultimately we alert the user that it failed
        assert received[-1]["args"][0] == {"success": False}

    def test_time_limit(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        socketio_client: SocketIOTestClient,
    ) -> None:
        """Ensure tasks exceeding the time limit are dealt with properly."""
        socketio_client.get_received()

        mocker.patch(
            "matl_online.tasks.socket",
            new_callable=_get_socket_for_client(socketio_client),
        )

        ev = mocker.patch("matl_online.tasks.matl_task.octave.eval")
        ev.side_effect = SoftTimeLimitExceeded

        with pytest.raises(SoftTimeLimitExceeded):
            matl_task(
                "-ro",
                "1D",
                "",
                "20.0.0",
                session_id_for_client(socketio_client),
            )

        received = socketio_client.get_received()

        payload = received[0]["args"][0]

        assert payload.get("session") == session_id_for_client(socketio_client)
        assert payload["data"][0]["type"] == "stderr"
        assert payload["data"][0]["value"] == "Operation timed out"

        assert received[-1]["args"][0] == {"success": False}
