import oct2py
import os

from celery import Task
from celery.task.control import revoke
from flask_socketio import SocketIO

from matl_online.settings import Config
from matl_online.extensions import celery
from matl_online.matl import matl


class OctaveTask(Task):
    abstract = True
    _octave = None
    _socket = None

    @property
    def octave(self):
        if self._octave is None:
            self._octave = oct2py.Oct2Py()
            self.after_return()
        return self._octave

    @property
    def socket(self):
        if self._socket is None:
            self._socket = SocketIO(message_queue='redis://')
        return self._socket

    def after_return(self, *args, **kwargs):
        # This is where we clean up octave
        self.octave.restoredefaultpath()
        self.octave.source(os.path.join(Config.MATL_WRAP_DIR, '.octaverc'))
        self.octave.addpath(os.path.join(Config.MATL_WRAP_DIR))

    def on_failure(self, *args, **kwargs):
        # TODO: Cleanup temporary folder
        #payload = {'data': [{'type': 'stderr', 'value': 'Server Error'}]}
        #matl_task.socket.emit('status', payload)
        pass


@celery.task()
def killtask(taskid, sessionid):
    revoke(taskid, terminate=True)


@celery.task(base=OctaveTask, bind=True)
def matl_task(self, *args, **kwargs):
    session_id = kwargs.get('session', '')
    output = matl(matl_task.octave, *args, **kwargs)
    result = {'data': output, 'session': session_id}

    # Fire off an event to the client with the output
    matl_task.socket.emit('status', result,
                          room=session_id)

    return result
