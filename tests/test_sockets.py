from matl_online.extensions import socketio


class TestSockets:

    def test_connection(self, socketclient):
        events = socketclient.get_received()

        assert len(events) == 1
        assert events[0]['namespace'] == '/'
        assert events[0]['name'] == 'connection'

        payload = events[0]['args']

        assert len(payload) == 1
        assert 'session_id' in payload[0]
        assert payload[0]['session_id'] == socketclient.sid

    def test_submit_empty(self, socketclient, mocker):
        # No task code should be run for empty code input

        # Clear previous events
        socketclient.get_received()

        task = mocker.patch('matl_online.tasks.matl_task')

        socketclient.emit('submit',
                          {'uid': socketclient.sid, 'code': ''})

        assert len(socketclient.get_received()) == 0
        assert not task.called

    def test_real_submit(self, socketclient, mocker):
        # When we submit inputs and code the matl_task should be run

        socketclient.get_received()
        # The task ID should be stored in the session

        task = mocker.patch('matl_online.public.views.matl_task.delay')

        task_id = '12345'
        task.return_value = type('obj', (object,), {'id': task_id})

        socketclient.emit('submit',
                          {'uid': socketclient.sid,
                           'code': 'D',
                           'inputs': '1'})

        session = socketio.server.environ[socketclient.sid]['saved_session']

        assert task.call_count == 1
        assert session.get('taskid') == task_id
