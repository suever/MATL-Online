"""Unit tests for socket interaction between server and client."""

from matl_online.extensions import socketio
from .helpers import session_id_for_client


def session(client):
    """Retrieve a client's session."""
    return socketio.server.environ[client.sid].get('saved_session', {})


class TestSockets:
    """Series of tests to ensure the expected data is passed via sockets."""

    def test_connection(self, socketclient):
        """During initial connection, session ID's should be sent."""
        events = socketclient.get_received()

        assert len(events) == 1
        assert events[0]['namespace'] == '/'
        assert events[0]['name'] == 'connection'

        payload = events[0]['args']

        assert len(payload) == 1
        assert 'session_id' in payload[0]

        assert payload[0]['session_id'] == session_id_for_client(socketclient)

    def test_submit_empty(self, socketclient, mocker, db):
        """If no code is provided, no tasks should ever run."""
        # Clear previous events
        socketclient.get_received()

        task = mocker.patch('matl_online.tasks.matl_task')

        socketclient.emit('submit', {
            'uid': session_id_for_client(socketclient),
            'code': '',
        })

        assert len(socketclient.get_received()) == 0
        task.assert_not_called()

    def test_real_submit(self, socketclient, mocker, db):
        """A matl_task should run with valid inputs."""
        socketclient.get_received()
        # The task ID should be stored in the session

        task = mocker.patch('matl_online.public.views.matl_task.delay')

        task_id = '12345'
        task.return_value = type('obj', (object,), {'id': task_id})

        socketclient.emit('submit', {
            'uid': session_id_for_client(socketclient),
            'code': '0',
            'inputs': '1',
        })

        assert task.call_count == 1
        assert session(socketclient).get('taskid') == task_id

    def test_kill_task_no_task(self, socketclient, mocker):
        """Kill events for invalid tasks should be handled gracefully."""
        socketclient.get_received()

        mocker.patch('matl_online.tasks.matl_task')

        assert session(socketclient).get('taskid') is None

        # Try to kill a task without starting one
        socketclient.emit('kill', {})

        # We should get a confirmation back regardless
        received = socketclient.get_received()

        assert len(received) == 1

        payload = received[0]['args'][0]
        assert payload.get('message') == 'User terminated the job'
        assert payload.get('success') is False

        # Make sure that no task id was aassigned
        assert session(socketclient).get('taskid') is None

    def test_kill_task(self, socketclient, mocker, db):
        """Kill events result in a task being revoked and terminated."""
        socketclient.get_received()

        mocker.patch('matl_online.tasks.matl_task')
        revoke = mocker.patch('matl_online.public.views.celery.control.revoke')

        # Start a job to set the session variable
        self.test_real_submit(socketclient, mocker, db)

        # Get the task id
        taskid = session(socketclient).get('taskid')

        socketclient.emit('kill', {})

        # Make sure that a message was sent to kill the tasks
        revoke.assert_called_once_with(taskid, terminate=True, signal='SIGTERM')

        received = socketclient.get_received()

        assert len(received) == 1

        payload = received[0]['args'][0]
        assert payload.get('message') == 'User terminated the job'
        assert payload.get('success') is False

        # Make sure that the task id was cleared
        assert session(socketclient).get('taskid') is None
