import logging
import os
import pytest

from celery.exceptions import SoftTimeLimitExceeded
from matl_online.tasks import OctaveTask, OutputHandler, matl_task


def prepare_folder_testcase(mocker, moctave, tmpdir):
    mocker.patch('matl_online.tasks.Task')

    mktmp = mocker.patch('matl_online.tasks.tempfile.mkdtemp')
    mktmp.return_value = tmpdir.strpath

    gettmp = mocker.patch('matl_online.tasks.tempfile.gettempdir')
    gettmp.return_value = tmpdir.strpath


class TestOctaveTask:

    def test_octave_property(self, mocker, moctave, logger):
        mocker.patch('matl_online.tasks.Task')

        logger.setLevel(logging.ERROR)
        moctave.logger = logger

        task = OctaveTask()

        # Make sure that there is no _octave property
        assert task._octave is None

        newoctave = task.octave

        assert task._octave == newoctave
        assert newoctave == moctave

        # Check the logging level is appropriate
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], OutputHandler)
        assert logger.handlers[0] == task._handler

        return task

    def test_octave_property_repeat(self, mocker, moctave, logger):
        task = self.test_octave_property(mocker, moctave, logger)

        # Get the property again and make sure we don't add any more
        # handlers
        task.octave

        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], OutputHandler)
        assert logger.handlers[0] == task._handler

    def test_folder_no_session(self, mocker, moctave, tmpdir):
        prepare_folder_testcase(mocker, moctave, tmpdir)

        task = OctaveTask()

        assert os.path.isdir(tmpdir.strpath)
        assert task.folder == tmpdir.strpath
        assert os.path.isdir(tmpdir.strpath)

    def test_folder_with_session(self, mocker, moctave, tmpdir):
        prepare_folder_testcase(mocker, moctave, tmpdir)

        task = OctaveTask()
        ID = '123456'
        task.session_id = ID

        outfolder = os.path.join(tmpdir.strpath, ID)

        assert not os.path.isdir(outfolder)
        assert task.folder == outfolder
        assert os.path.isdir(outfolder)

    def test_on_term(self, mocker, moctave):
        initialize = mocker.patch('matl_online.tasks._initialize_process')

        task = OctaveTask()

        # Hopefully we kill the current thing, restart octave, and
        # initialize
        task.on_term()

        methods = [m[0] for m in moctave.method_calls]

        assert 'restart' in methods
        assert '_session.interrupt' in methods
        assert initialize.called


class TestMATLTask:

    def test_normal(self, mocker, moctave, socketclient):
        # Clear out the socket client's messages so far
        socketclient.get_received()

        # Overload the use of the message_queue by simply mocking the
        # socket instance in tasks.py
        mocker.patch('matl_online.tasks.socket',
                     new_callable=lambda: socketclient.socketio)

        matl_task.delay('-ro', '1D', session=socketclient.sid).wait()

        received = socketclient.get_received()
        assert received[-1]['args'][0] == {'message': '', 'success': True}

    def test_keyboard_interupt(self, mocker, moctave, socketclient):

        socketclient.get_received()

        mocker.patch('matl_online.tasks.socket',
                     new_callable=lambda: socketclient.socketio)

        E = mocker.patch('matl_online.tasks.matl_task._octave.eval')
        E.side_effect = KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            matl_task.delay('-ro', '1D', session=socketclient.sid).wait()

        received = socketclient.get_received()

        payload = received[0]['args'][0]

        assert payload.get('session') == socketclient.sid
        assert payload['data'][0]['type'] == 'stderr'
        assert payload['data'][0]['value'] == 'Job cancelled'

        # Ultimately we alert the user that it failed
        assert received[-1]['args'][0] == {'success': False}

    def test_time_limit(self, mocker, moctave, socketclient):

        socketclient.get_received()

        mocker.patch('matl_online.tasks.socket',
                     new_callable=lambda: socketclient.socketio)

        E = mocker.patch('matl_online.tasks.matl_task._octave.eval')
        E.side_effect = SoftTimeLimitExceeded

        # TODO: We shouldn't have to explicitly clear this
        matl_task.octave.logger.handlers[0].clear()

        with pytest.raises(SoftTimeLimitExceeded):
            matl_task.delay('-ro', '1D', session=socketclient.sid).wait()

        received = socketclient.get_received()

        payload = received[0]['args'][0]

        assert payload.get('session') == socketclient.sid
        assert payload['data'][0]['type'] == 'stderr'
        assert payload['data'][0]['value'] == 'Operation timed out'

        assert received[-1]['args'][0] == {'success': False}
