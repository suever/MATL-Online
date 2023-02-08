"""Unit tests for checking our realtime log handler."""

from logging import Logger

from pytest_mock.plugin import MockerFixture

from matl_online.tasks import OctaveTask, OutputHandler


class TestLogHandler:
    """Series of tests for the OutputHandler logging handler."""

    def test_initialization(self, logger: Logger) -> None:
        """Make sure that all necessary properties are set."""
        task = OctaveTask()
        task.session_id = "123"
        handler = OutputHandler(task)
        logger.addHandler(handler)

        assert handler.task == task

        # There should be no messages initially
        assert len(handler.contents) == 0
        assert handler.messages() == ""

    def test_stdout_log(self, logger: Logger) -> None:
        """STDOUT events should create appropriate messages."""
        task = OctaveTask()
        task.session_id = "123"
        handler = OutputHandler(task)
        logger.addHandler(handler)

        # Write something to the log
        msg = "I am a message"
        logger.info(msg)

        assert len(handler.contents) == 1
        assert handler.messages() == msg

    def test_clc_log(self, logger: Logger, mocker: MockerFixture) -> None:
        """CLC should flush the contents."""
        task = OctaveTask()
        task.session_id = "123"
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch("matl_online.tasks.OutputHandler.send")

        # Write something to the log
        logger.info("I am an empty message")

        send_func.assert_not_called()
        assert len(handler.contents) == 1

        # Now send a CLC event
        logger.info("[CLC]")

        # Make sure that the send function was called
        assert send_func.call_count == 1

        # Make sure all messages were flushed
        assert len(handler.contents) == 0

    def test_pause(self, logger: Logger, mocker: MockerFixture) -> None:
        """For a pause event, we should have data sent but NOT cleared."""
        task = OctaveTask()
        task.session_id = "123"
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch("matl_online.tasks.OutputHandler.send")

        msg = "I am an empty message"

        # Write something to the log
        logger.info(msg)

        send_func.assert_not_called()
        assert len(handler.contents) == 1

        # Now send a CLC event
        logger.info("[PAUSE]")

        # Make sure that the send function was called
        assert send_func.call_count == 1

        # Make sure all messages were flushed
        assert len(handler.contents) == 1
        assert handler.messages() == msg

    def test_ignore_octave_warning(self, logger: Logger, mocker: MockerFixture) -> None:
        """Occasionally octave will print warning: messages to be ignored."""
        task = OctaveTask()
        task.session_id = "123"
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch("matl_online.tasks.OutputHandler.send")

        logger.info("warning: I am octave and I like warnings")
        logger.info("warning: I am octave and I still like warnings")

        send_func.assert_not_called()
        assert len(handler.contents) == 0

    def test_matl_error_handling(self, logger: Logger, mocker: MockerFixture) -> None:
        """Error messages are prefaced with [STDERR]."""
        task = OctaveTask()
        task.session_id = "123"
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch("matl_online.tasks.OutputHandler.send")

        errmsg = "MATL run-time error:\nline 1\nline 2"
        logger.info(errmsg)

        # Check the contents
        send_func.assert_not_called()
        assert len(handler.contents) == 3
        assert handler.contents[0] == "[STDERR]MATL run-time error:"
        assert handler.contents[1] == "[STDERR]line 1"
        assert handler.contents[2] == "[STDERR]line 2"

    def test_filter(self, logger: Logger, mocker: MockerFixture) -> None:
        """Ensure that we ONLY get info events."""
        task = OctaveTask()
        task.session_id = "123"
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch("matl_online.tasks.OutputHandler.send")

        logger.warning("warning")
        logger.error("error")
        logger.debug("debug")

        assert len(handler.contents) == 0
        send_func.assert_not_called()

    def test_send(self, logger: Logger, mocker: MockerFixture) -> None:
        """Make sure socket events are issued as expected."""
        identifier = "123"
        task = OctaveTask()
        task.session_id = identifier
        handler = OutputHandler(task)
        logger.addHandler(handler)

        emit = mocker.patch("matl_online.tasks.socket.emit")

        logger.info("test1")
        logger.info("[STDERR]error")
        handler.send()

        assert emit.called == 1
        assert len(emit.call_args) == 2

        event, payload = emit.call_args[0]

        expected_data = {
            "session": identifier,
            "data": [
                {"type": "stdout", "value": "test1"},
                {"type": "stderr", "value": "error"},
            ],
        }

        assert payload == expected_data
        assert event == "status"
        assert emit.call_args[1].get("room") == identifier
