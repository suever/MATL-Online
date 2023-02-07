"""Unit tests for basic celery task functionality."""

import logging
import os

import pytest
from celery.exceptions import SoftTimeLimitExceeded

from matl_online.tasks import OctaveTask, matl_task

from .helpers import session_id_for_client


def prepare_folder_testcase(mocker, tmpdir):
    """Create the necessary mocks."""
    mocker.patch("matl_online.tasks.Task")

    make_directory_mock = mocker.patch("matl_online.tasks.tempfile.mkdtemp")
    make_directory_mock.return_value = tmpdir.strpath

    get_temporary_directory_mock = mocker.patch("matl_online.tasks.tempfile.gettempdir")
    get_temporary_directory_mock.return_value = tmpdir.strpath


class TestOctaveTask:
    """Series of tests for the OctaveTask class."""

    def test_octave_property(self, mocker, octave_mock, logger):
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

    def test_octave_property_repeat(self, mocker, octave_mock, logger):
        """Octave sessions are only created once per task."""
        task = self.test_octave_property(mocker, octave_mock, logger)

        # Get the property again and make sure we don't create a new
        # instance
        assert task.octave == octave_mock

    def test_folder_no_session(self, mocker, octave_mock, tmpdir):
        """Test the dynamic folder property when there is no session."""
        prepare_folder_testcase(mocker, tmpdir)

        task = OctaveTask()

        assert os.path.isdir(tmpdir.strpath)
        assert task.folder == tmpdir.strpath
        assert os.path.isdir(tmpdir.strpath)

    def test_folder_with_session(self, mocker, octave_mock, tmpdir):
        """Test the folder property when we DO have a session."""
        prepare_folder_testcase(mocker, tmpdir)

        task = OctaveTask()
        session_id = "123456"
        task.session_id = session_id

        output_directory = os.path.join(tmpdir.strpath, session_id)

        assert not os.path.isdir(output_directory)
        assert task.folder == output_directory
        assert os.path.isdir(output_directory)

    def test_on_term(self, mocker, octave_mock):
        """Ensure cleanup is performed as expected when a task is terminated."""
        initialize = mocker.patch("matl_online.tasks._initialize_process")

        task = OctaveTask()

        # Hopefully we kill the current thing, restart octave, and
        # initialize
        task.on_term()

        methods = [m[0] for m in octave_mock.method_calls]

        assert "restart" in methods
        assert initialize.call_count == 1


class TestMATLTask:
    """Tests for the MATLTask subclass of OctaveTask."""

    def test_normal(self, mocker, octave_mock, socketio_client):
        """Test that messages are received as expected in normal case."""
        # Clear out the socket client's messages so far
        socketio_client.get_received()

        # Overload the use of the message_queue by simply mocking the
        # socket instance in tasks.py
        mocker.patch(
            "matl_online.tasks.socket", new_callable=lambda: socketio_client.socketio
        )

        matl_task("-ro", "1D", session=session_id_for_client(socketio_client))

        received = socketio_client.get_received()
        assert received[-1]["args"][0] == {"message": "", "success": True}

    def test_keyboard_interrupt(self, mocker, octave_mock, socketio_client):
        """Ensure proper handling of keyboard interrupt events."""
        socketio_client.get_received()

        mocker.patch(
            "matl_online.tasks.socket", new_callable=lambda: socketio_client.socketio
        )

        ev = mocker.patch("matl_online.tasks.matl_task.octave.eval")
        ev.side_effect = KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            matl_task("-ro", "1D", session=session_id_for_client(socketio_client))

        received = socketio_client.get_received()

        payload = received[0]["args"][0]

        assert payload.get("session") == session_id_for_client(socketio_client)
        assert payload["data"][0]["type"] == "stderr"
        assert payload["data"][0]["value"] == "Job cancelled"

        # Ultimately we alert the user that it failed
        assert received[-1]["args"][0] == {"success": False}

    def test_time_limit(self, mocker, octave_mock, socketio_client):
        """Ensure tasks exceeding the time limit are dealt with properly."""
        socketio_client.get_received()

        mocker.patch(
            "matl_online.tasks.socket", new_callable=lambda: socketio_client.socketio
        )

        ev = mocker.patch("matl_online.tasks.matl_task.octave.eval")
        ev.side_effect = SoftTimeLimitExceeded

        with pytest.raises(SoftTimeLimitExceeded):
            matl_task("-ro", "1D", session=session_id_for_client(socketio_client))

        received = socketio_client.get_received()

        payload = received[0]["args"][0]

        assert payload.get("session") == session_id_for_client(socketio_client)
        assert payload["data"][0]["type"] == "stderr"
        assert payload["data"][0]["value"] == "Operation timed out"

        assert received[-1]["args"][0] == {"success": False}
