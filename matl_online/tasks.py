import os
import tempfile
import shutil

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import worker_process_init
from celery.task.control import revoke

from flask_socketio import SocketIO

from matl_online.settings import Config
from matl_online.extensions import celery
from matl_online.matl import matl

octave = None
socket = SocketIO(message_queue='redis://')


class OctaveTask(Task):
    abstract = True
    _octave = None
    _tempfolder = None
    session_id = None

    def __init__(self, *args, **kwargs):
        super(OctaveTask, self).__init__(*args, **kwargs)

    @property
    def octave(self):
        if self._octave is None:
            # We hide this import within this property getter so that
            # non-worker processes don't start up an octave instance. This
            # simply gets the octave session which should already be
            # initiailized by _initialize_process
            from oct2py import octave
            self._octave = octave
        return self._octave

    @property
    def folder(self):
        if self._tempfolder is None:
            # Generate the temporary folder
            if self.session_id:
                self._tempfolder = os.path.join(tempfile.gettempdir(),
                                                self.session_id)
            else:
                self._tempfolder = tempfile.mkdtemp()

        # Make directory if it doesn't exist
        if not os.path.isdir(self._tempfolder):
            os.makedirs(self._tempfolder)

        return self._tempfolder

    def emit(self, *args, **kwargs):
        socket.emit(*args, room=self.session_id, **kwargs)

    def cleanup(self):
        # Go ahead and kill octave
        self.octave._session.interrupt()

        # Remove all temporary files
        self.clean_folders()

        # Get it running again
        self.octave.restart()
        _initialize_process()

    def clean_folders(self):
        if os.path.isdir(self.folder):
            shutil.rmtree(self.folder)

    def on_success(self, *args, **kwargs):
        self.clean_folders()

    def on_failure(self, *args, **kwargs):
        # Send a message that we failed
        self.emit('complete', {'success': False})
        self.cleanup()


@celery.task()
def killtask(taskid, sessionid):
    """
    Simple task for killing a currently-running job.
    """
    revoke(taskid, terminate=True)


@celery.task(base=OctaveTask, bind=True)
def matl_task(self, *args, **kwargs):
    """
    Celery for processing a MATL command and returning the result
    """

    self.session_id = kwargs.pop('session', '')

    try:
        output = matl(matl_task.octave, *args,
                      folder=self.folder, **kwargs)

        result = {'data': output, 'session': self.session_id}

        # Fire off an event to the client with the output
        self.emit('status', result)

        self.emit('complete', {'success': True})

    # In the case of an interrupt (either through a time limit or a
    # revoke() event, we will still clean things up
    except (KeyboardInterrupt, SystemExit, SoftTimeLimitExceeded):
        print 'term event'
        # Clean things up
        self.cleanup()

        # Propagate the term event up the chain to actually kill the worker
        raise

    return result


def _initialize_process(**kwargs):
    """
    Function to be called when a worker process is spawned. We use this to
    opportunity to actually launch octave and execute a quick MATL program
    """

    # Import oct2py within here because it creates a new instance of octave
    import oct2py

    # Run MATL for the first time to initialize everything
    oct2py.octave.source(os.path.join(Config.MATL_WRAP_DIR, '.octaverc'))
    oct2py.octave.addpath(os.path.join(Config.MATL_WRAP_DIR))
    matl(oct2py.octave, '-h', folder=tempfile.mkdtemp())

# When a worker process is spawned, initialize octave
worker_process_init.connect(_initialize_process)
