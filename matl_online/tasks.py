"""Celery tasks for running MATL programs."""

import logging
import os
import shutil
import tempfile
from logging import StreamHandler

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import worker_process_init
from flask_socketio import SocketIO

from matl_online.extensions import celery
from matl_online.matl import matl, parse_matl_results
from matl_online.octave import OctaveSession
from matl_online.settings import config

octave = None

socket = SocketIO(message_queue=config.SOCKETIO_MESSAGE_QUEUE)


class OutputHandler(StreamHandler):
    """Custom handler for converting logged data to socket events."""

    def __init__(self, task, *args, **kwargs):
        """Initialize the handler with the task we are handling."""
        StreamHandler.__init__(self, *args, **kwargs)
        self.task = task
        self.clear()

    def clear(self):
        """Clear all messages that have been logged so far."""
        self.contents = []

    def messages(self):
        """Concatenate all messages into a long stream."""
        return "\n".join([x for x in self.contents])

    def send(self):
        """Send a message out to the specified rooms."""
        output = parse_matl_results(self.messages())
        result = {"data": output, "session": self.task.session_id}
        socket.emit("status", result, room=self.task.session_id)
        return result

    def emit(self, record):
        """Overloaded emit method to receive LogRecord instances."""
        # Look to see if there are any special commands in here. These
        # commands will clear the output:
        #
        #   1. [PAUSE]  Send everything that we have so far
        #   2. [CLC]    Send an empty message and clear contents
        #   3. [IMAGE]  FUTURE ENCODING TO BASE64

        if record.levelno == logging.INFO:
            self.process_message(record.msg)

    def process_message(self, message):
        """Append a message to be send back to the user."""
        print(message)

        if message == "[PAUSE]":
            # For now we send the entire message again. Consider a better
            # approach (i.e. adding a field to the result that says to
            # flush prior to display)
            self.send()
            return
        elif message == "[CLC]":
            self.send()
            self.clear()
            return
        elif message.startswith("warning:"):
            return
        elif message.startswith("MATL run-time error:"):
            for item in message.split("\n"):
                self.contents.append("[STDERR]" + item)

            return

        self.contents.append(message)


class OctaveTask(Task):
    """Custom Task type for interacting with octave."""

    abstract = True
    _octave = None
    _tempfolder = None
    session_id = None
    _handler = None

    def __init__(self, *args, **kwargs):
        """Initialize task."""
        global octave
        super(OctaveTask, self).__init__(*args, **kwargs)

    @property
    def octave(self):
        """Dependent property which automatically spawns octave if needed."""
        if self._octave is None:
            global octave
            self._octave = octave

        return self._octave

    @property
    def handler(self):
        """Dependent property that creates an OutputHandler instance."""
        if self._handler is None:
            self._handler = OutputHandler(self)

        return self._handler

    @property
    def folder(self):
        """Dependent property that creates a session-specific folder if needed."""
        if self._tempfolder is None:
            # Generate the temporary folder
            if self.session_id:
                self._tempfolder = os.path.join(tempfile.gettempdir(), self.session_id)
            else:
                self._tempfolder = tempfile.mkdtemp()

        # Make directory if it doesn't exist
        if not os.path.isdir(self._tempfolder):
            os.makedirs(self._tempfolder)

        return self._tempfolder

    def emit(self, *args, **kwargs):
        """Send an event to any listening clients."""
        socket.emit(*args, room=self.session_id, **kwargs)

    def on_term(self):
        """Clean up after termination event."""
        # Restart octave so we're ready to go with future calls
        self.octave.restart()
        _initialize_process()

    def on_success(self, *args, **kwargs):
        """Send a completion messages upon successful completion."""
        self.emit("complete", {"success": True, "message": ""})

    def on_kill(self):
        """Clean up after a task is killed.

        This is a hard kill by celery so this worker will be destroyed. No
        need to restart octave
        """
        self.octave._engine.repl.terminate()
        self.on_failure()

    def send_results(self):
        """Local forwarder for all send events."""
        return self.handler.send()

    def after_return(self, *args, **kwargs):
        """Fire after task completion."""
        self.handler.clear()

        if os.path.isdir(self.folder):
            shutil.rmtree(self.folder)

    def on_failure(self, *args, **kwargs):
        """Send a message if the task failed for any reason."""
        self.send_results()
        self.emit("complete", {"success": False})


@celery.task(base=OctaveTask, bind=True)
def matl_task(self, *args, **kwargs):
    """Celery task for processing a MATL command and returning the result."""
    self.session_id = kwargs.pop("session", "")
    self.handler.clear()

    is_test = config.ENV == "test"

    try:
        matl(
            self.octave,
            *args,
            folder=self.folder,
            line_handler=self.handler.process_message,
            **kwargs,
        )
        result = self.send_results()

    # In the case of an interrupt (either through a time limit or a
    # revoke() event, we will still clean things up
    except (KeyboardInterrupt, SystemExit):
        self.handler.process_message("[STDERR]Job cancelled")
        self.on_kill()
        raise
    except SoftTimeLimitExceeded:
        # Propagate the term event up the chain to actually kill the worker
        self.handler.process_message("[STDERR]Operation timed out")
        self.on_term()

        if is_test:
            self.on_failure()
            self.after_return()

        raise

    if is_test:
        self.on_success()
        self.after_return()

    return result


def _initialize_process(**kwargs):
    """Initialize the the octave instance.

    Function to be called when a worker process is spawned. We use this to
    opportunity to actually launch octave and execute a quick MATL program
    """
    global octave

    octave = OctaveSession(octaverc=config.OCTAVERC, paths=[config.MATL_WRAP_DIR])


# When a worker process is spawned, initialize octave
worker_process_init.connect(_initialize_process)
