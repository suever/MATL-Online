"""Unit tests for checking our realtime log handler."""

from matl_online.tasks import OutputHandler


class TestLogHandler:
    """Series of tests for the OutputHandler logging handler."""

    def test_initialization(self, logger):
        """Make sure that all necessary properties are set."""
        task = type('task', (object,), {'session_id': '123'})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        assert handler.task == task

        # There should be no messages initially
        assert len(handler.contents) == 0
        assert handler.messages() == ''

    def test_stdout_log(self, logger):
        """STDOUT events should create appropriate messages."""
        task = type('task', (object,), {'session_id': '123'})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        # Write something to the log
        msg = 'I am a message'
        logger.info(msg)

        assert len(handler.contents) == 1
        assert handler.messages() == msg

    def test_clc_log(self, logger, mocker):
        """CLC should flush the contents."""
        task = type('task', (object,), {'session_id': '123'})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch('matl_online.tasks.OutputHandler.send')

        # Write something to the log
        logger.info('I am an empty message')

        send_func.assert_not_called()
        assert len(handler.contents) == 1

        # Now send a CLC event
        logger.info('[CLC]')

        # Make sure that the send function was called
        assert send_func.call_count == 1

        # Make sure all messages were flushed
        assert len(handler.contents) == 0

    def test_pause(self, logger, mocker):
        """For a pause event, we should have data sent but NOT cleared."""
        task = type('task', (object,), {'session_id': '123'})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch('matl_online.tasks.OutputHandler.send')

        msg = 'I am an empty message'

        # Write something to the log
        logger.info(msg)

        send_func.assert_not_called()
        assert len(handler.contents) == 1

        # Now send a CLC event
        logger.info('[PAUSE]')

        # Make sure that the send function was called
        assert send_func.call_count == 1

        # Make sure all messages were flushed
        assert len(handler.contents) == 1
        assert handler.messages() == msg

    def test_ignore_octave_warning(self, logger, mocker):
        """Occassionally octave will print warning: messages to be ignored."""
        task = type('task', (object,), {'session_id': '123'})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch('matl_online.tasks.OutputHandler.send')

        logger.info('warning: I am octave and I like warnings')
        logger.info('warning: I am octave and I still like warnings')

        send_func.assert_not_called()
        assert len(handler.contents) == 0

    def test_matl_error_handling(self, logger, mocker):
        """Error messages are prefaced with [STDERR]."""
        task = type('task', (object,), {'session_id': '123'})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch('matl_online.tasks.OutputHandler.send')

        errmsg = 'MATL run-time error:\nline 1\nline 2'
        logger.info(errmsg)

        # Check the contents
        send_func.assert_not_called()
        assert len(handler.contents) == 3
        assert handler.contents[0].msg == '[STDERR]MATL run-time error:'
        assert handler.contents[1].msg == '[STDERR]line 1'
        assert handler.contents[2].msg == '[STDERR]line 2'

    def test_filter(self, logger, mocker):
        """Ensure that we ONLY get info events."""
        task = type('task', (object,), {'session_id': '123'})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        send_func = mocker.patch('matl_online.tasks.OutputHandler.send')

        logger.warn('warning')
        logger.error('error')
        logger.debug('debug')

        assert len(handler.contents) == 0
        send_func.assert_not_called()

    def test_send(self, logger, mocker):
        """Make sure socket events are issued as expected."""
        identifier = '123'
        task = type('task', (object,), {'session_id': identifier})
        handler = OutputHandler(task)
        logger.addHandler(handler)

        emit = mocker.patch('matl_online.tasks.socket.emit')

        logger.info('test1')
        logger.info('[STDERR]error')
        handler.send()

        assert emit.called == 1
        assert len(emit.call_args) == 2

        event, payload = emit.call_args[0]

        # TODO: Look into if we really want a trailing newline here
        expected_data = {'session': identifier,
                         'data': [{'type': 'stdout', 'value': 'test1\n'},
                                  {'type': 'stderr', 'value': 'error'}]}

        assert payload == expected_data
        assert event == 'status'
        assert emit.call_args[1].get('room') == identifier
