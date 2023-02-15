"""Unit tests for basic celery task functionality."""

import pathlib
from typing import Callable
from unittest.mock import Mock

import pytest
from celery.exceptions import SoftTimeLimitExceeded
from flask_socketio import SocketIO, SocketIOTestClient  # type: ignore[import]
from pytest_mock.plugin import MockerFixture

from matl_online.tasks import OctaveTask, _initialize_process, matl_task
from matl_online.types import MATLRunTaskParameters

from .helpers import session_id_for_client


class TestOctaveTask:
    """Series of tests for the OctaveTask class."""

    def test_on_term(self, octave_mock: Mock) -> None:
        """Ensure cleanup is performed as expected when a task is terminated."""
        task = OctaveTask()

        task.on_term()

        octave_mock.restart.assert_called_once()


def _get_socketio_for_client(client: SocketIOTestClient) -> Callable[[], SocketIO]:
    return lambda: client.socketio


class TestProcessInitialization:
    def test_octave_initialization(
        self,
        octave_mock: Mock,
        mocker: MockerFixture,
    ) -> None:
        patch = mocker.patch(
            "matl_online.tasks.OctaveSession",
            return_value=octave_mock,
        )

        # When initializing the process
        _initialize_process()

        # Then the octave session was created
        patch.assert_called_once()


class TestMATLTask:
    """Tests for the MATLTask subclass of OctaveTask."""

    def test_normal(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        socketio_client: SocketIOTestClient,
        tmp_path: pathlib.Path,
    ) -> None:
        """Test that messages are received as expected in normal case."""
        # Clear out the socket client's messages so far
        socketio_client.get_received()

        # Overload the use of the message_queue by simply mocking the
        # socket instance in tasks.py
        mocker.patch(
            "matl_online.tasks.socket",
            new_callable=_get_socketio_for_client(socketio_client),
        )

        mocker.patch("matl_online.matl.core.get_matl_folder", return_value=tmp_path)
        matl_task.apply(
            args=(
                MATLRunTaskParameters(
                    code="1D",
                    version="20.0.0",
                    session_id=session_id_for_client(socketio_client),
                ),
            ),
        )

        received = socketio_client.get_received()
        assert received[-1]["args"][0] == {"message": "", "success": True}

    def test_exception(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        socketio_client: SocketIOTestClient,
        tmp_path: pathlib.Path,
    ) -> None:
        """Ensure proper handling of keyboard interrupt events."""
        socketio_client.get_received()

        mocker.patch(
            "matl_online.tasks.socket",
            new_callable=_get_socketio_for_client(socketio_client),
        )

        mocker.patch("matl_online.matl.core.get_matl_folder", return_value=tmp_path)

        ev = mocker.patch("matl_online.tasks.matl_task.octave.run")
        ev.side_effect = Exception("Test")

        matl_task.apply(
            args=(
                MATLRunTaskParameters(
                    code="1D",
                    version="20.0.0",
                    session_id=session_id_for_client(socketio_client),
                ),
            ),
        )

        received = socketio_client.get_received()

        payload = received[0]["args"][0]

        assert payload.get("session") == session_id_for_client(socketio_client)
        assert payload["data"][0]["type"] == "stderr"
        assert payload["data"][0]["value"] == "Unknown error"

        # Ultimately we alert the user that it failed
        assert received[-1]["args"][0] == {"success": False}

    def test_keyboard_interrupt(
        self,
        mocker: MockerFixture,
        octave_mock: Mock,
        socketio_client: SocketIOTestClient,
        tmp_path: pathlib.Path,
    ) -> None:
        """Ensure proper handling of keyboard interrupt events."""
        socketio_client.get_received()

        mocker.patch(
            "matl_online.tasks.socket",
            new_callable=_get_socketio_for_client(socketio_client),
        )

        mocker.patch("matl_online.matl.core.get_matl_folder", return_value=tmp_path)

        ev = mocker.patch("matl_online.tasks.matl_task.octave.run")
        ev.side_effect = KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            matl_task.apply(
                args=(
                    MATLRunTaskParameters(
                        code="1D",
                        version="20.0.0",
                        session_id=session_id_for_client(socketio_client),
                    ),
                ),
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
        tmp_path: pathlib.Path,
    ) -> None:
        """Ensure tasks exceeding the time limit are dealt with properly."""
        socketio_client.get_received()

        mocker.patch(
            "matl_online.tasks.socket",
            new_callable=_get_socketio_for_client(socketio_client),
        )

        ev = mocker.patch("matl_online.tasks.matl_task.octave.run")
        ev.side_effect = SoftTimeLimitExceeded

        mocker.patch("matl_online.matl.core.get_matl_folder", return_value=tmp_path)

        matl_task.apply(
            args=(
                MATLRunTaskParameters(
                    code="1D",
                    version="20.0.0",
                    session_id=session_id_for_client(socketio_client),
                ),
            ),
        )

        received = socketio_client.get_received()

        payload = received[0]["args"][0]

        assert payload.get("session") == session_id_for_client(socketio_client)
        assert payload["data"][0]["type"] == "stderr"
        assert payload["data"][0]["value"] == "Operation timed out"

        assert received[-1]["args"][0] == {"success": False}
