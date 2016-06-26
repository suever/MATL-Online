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
from matl_online.matl import matl, parse_matl_results

from logging import StreamHandler
import logging

octave = None
socket = SocketIO(message_queue='redis://')


class OutputHandler(StreamHandler):
    def __init__(self, task, *args, **kwargs):
        """ Initialize the handler with the task we are handling """
        StreamHandler.__init__(self, *args, **kwargs)
        self.task = task
        self.clear()

    def clear(self):
        """ Clears all messages that have been logged so far """
        self.contents = []

    def getMessages(self):
        """ Concatenates all messages into a long stream """
        return '\n'.join([x.getMessage() for x in self.contents])

    def send(self):
        """ Send a message out to the specified rooms """
        output = parse_matl_results(self.getMessages())
        result = {'data': output, 'session': self.task.session_id}
        socket.emit('status', result, room=self.task.session_id)
        return result

    def emit(self, record):
        """ Overloaded emit method to receive LogRecord instances """

        # Look to see if there are any special commands in here. These
        # commands will clear the output:
        #
        #   1. [PAUSE]  Send everything that we have so far
        #   2. [CLC]    Send an empty message and clear contents
        #   3. [IMAGE]  FUTURE ENCODING TO BASE64

        if not record.levelno == logging.DEBUG:
            return

        if record.msg == '[PAUSE]':
            # For now we send the entire message again. Consider a better
            # approach (i.e. adding a field to the result that says to
            # flush prior to display)
            self.send()
            return
        elif record.msg == '[CLC]':
            self.send()
            self.clear()
            return
        elif record.msg.startswith('MATL run-time error:'):
            import copy
            for item in record.msg.split('\n'):
                newrecord = copy.copy(record)
                newrecord.msg = '[STDERR]' + item
                print newrecord.msg
                self.contents.append(newrecord)

            return
        elif record.msg.startswith('---'):
            return

        self.contents.append(record)


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

            # Setup handler
            self._handler = OutputHandler(self)

            # Remove all other handlers (stdout, etc.)
            self._octave.logger.handlers = []

            # Turn on debugging so we get notified of EVERY output as it
            # happens rather than waiting for a command to finish which is
            # what happens if we set the log level to INFO instead
            self._octave.logger.setLevel(logging.DEBUG)

            # Add our custom handler to capture all output
            self._octave.logger.addHandler(self._handler)
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

    def on_term(self):
        self.send_results()
        self.cleanup()

    def clean_folders(self):
        if os.path.isdir(self.folder):
            shutil.rmtree(self.folder)

        # Clear any messages from the handler
        self._handler.clear()

    def on_success(self, *args, **kwargs):
        self.emit('complete', {'success': True})
        self.clean_folders()

    def send_results(self):
        """ Local forwarder for all send events """
        return self._handler.send()

    def on_failure(self, *args, **kwargs):
        # Send a message that we failed
        self.send_results()
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
        matl(matl_task.octave, *args, folder=self.folder, **kwargs)
        result = self.send_results()

    # In the case of an interrupt (either through a time limit or a
    # revoke() event, we will still clean things up
    except (KeyboardInterrupt, SystemExit, SoftTimeLimitExceeded):
        print 'term event'
        # Clean things up
        self.on_term()

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
