"""Celery tasks for running MATL programs."""
from __future__ import annotations

import logging
import os
import pathlib
import shutil
import tempfile
from logging import LogRecord, StreamHandler
from typing import Any, Dict, List, Optional

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import worker_process_init
from flask_socketio import SocketIO  # type: ignore

from matl_online.extensions import celery
from matl_online.matl import matl, parse_matl_results
from matl_online.octave import OctaveSession
from matl_online.settings import config

octave = None

socket = SocketIO(message_queue=config.SOCKETIO_MESSAGE_QUEUE)

Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined]


class OutputHandler(StreamHandler):  # type: ignore
    """Custom handler for converting logged data to socket events."""

    contents: List[str]
    task: "OctaveTask"

    def __init__(
        self,
        task: "OctaveTask",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the handler with the task we are handling."""
        StreamHandler.__init__(self, *args, **kwargs)
        self.task = task
        self.contents = []

    def clear(self) -> None:
        """Clear all messages that have been logged so far."""
        self.contents = []

    def messages(self) -> str:
        """Concatenate all messages into a long stream."""
        return "\n".join([x for x in self.contents])

    def send(self) -> Dict[str, Any]:
        """Send a message out to the specified rooms."""
        output = parse_matl_results(self.messages())
        result = {"data": output, "session": self.task.session_id}
        socket.emit("status", result, room=self.task.session_id)
        return result

    def emit(self, record: LogRecord) -> None:
        """Overloaded emit method to receive LogRecord instances."""
        # Look to see if there are any special commands in here. These
        # commands will clear the output:
        #
        #   1. [PAUSE]  Send everything that we have so far
        #   2. [CLC]    Send an empty message and clear contents
        #   3. [IMAGE]  FUTURE ENCODING TO BASE64

        if record.levelno == logging.INFO:
            self.process_message(record.msg)

    def process_message(self, message: str) -> None:
        """Append a message to be sent back to the user."""
        print(message)

        if message == "[PAUSE]":
            # For now, we send the entire message again. Consider a better
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


class OctaveTask(Task[[str, str, str, str, Optional[str]], None]):
    """Custom Task type for interacting with octave."""

    abstract: bool = True
    _octave: Optional[OctaveSession] = None
    _tempfolder: Optional[pathlib.Path] = None
    session_id: Optional[str] = None
    _handler: Optional[OutputHandler] = None

    @property
    def octave(self) -> Optional[OctaveSession]:
        """Dependent property which automatically spawns octave if needed."""
        if self._octave is None:
            global octave
            self._octave = octave

        return self._octave

    @property
    def handler(self) -> OutputHandler:
        """Dependent property that creates an OutputHandler instance."""
        if self._handler is None:
            self._handler = OutputHandler(self)

        return self._handler

    @property
    def folder(self) -> pathlib.Path:
        """Dependent property that creates a session-specific folder if needed."""
        if self._tempfolder is None:
            # Generate the temporary folder
            if self.session_id:
                self._tempfolder = pathlib.Path(tempfile.gettempdir()).joinpath(
                    self.session_id
                )
            else:
                self._tempfolder = pathlib.Path(tempfile.mkdtemp())

        # Make directory if it doesn't exist
        if not self._tempfolder.is_dir():
            self._tempfolder.mkdir()

        return self._tempfolder

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """Send an event to any listening clients."""
        socket.emit(*args, room=self.session_id, **kwargs)

    def on_term(self) -> None:
        """Clean up after termination event."""
        # Restart octave, so we're ready to go with future calls
        if self.octave:
            self.octave.restart()

        _initialize_process()

    def on_success(self, *args: Any, **kwargs: Any) -> None:
        """Send a completion messages upon successful completion."""
        self.emit("complete", {"success": True, "message": ""})

    def on_kill(self) -> None:
        """Clean up after a task is killed.

        This is a hard kill by celery so this worker will be destroyed. No
        need to restart octave
        """
        if self.octave:
            self.octave.terminate()

        self.on_failure()

    def send_results(self) -> None:
        """Local forwarder for all send events."""
        self.handler.send()

    def after_return(self, *args: Any, **kwargs: Any) -> None:
        """Fire after task completion."""
        self.handler.clear()

        if os.path.isdir(self.folder):
            shutil.rmtree(self.folder)

    def on_failure(self, *args: Any, **kwargs: Any) -> None:
        """Send a message if the task failed for any reason."""
        self.send_results()
        self.emit("complete", {"success": False})


@celery.task(base=OctaveTask, bind=True)
def matl_task(
    task: OctaveTask,
    flags: str,
    code: str,
    inputs: str,
    version: str,
    session: str = "",
) -> None:
    """Celery task for processing a MATL command and returning the result."""
    task.session_id = session
    task.handler.clear()

    is_test = config.ENV == "test"

    if task.octave is None:
        raise Exception("Octave is not configured")

    try:
        matl(
            task.octave,
            flags,
            folder=task.folder,
            code=code,
            inputs=inputs,
            version=version,
            line_handler=task.handler.process_message,
        )

        task.send_results()

    # In the case of an interrupt (either through a time limit or a
    # revoke() event, we will still clean things up
    except (KeyboardInterrupt, SystemExit):
        task.handler.process_message("[STDERR]Job cancelled")
        task.on_kill()
        raise
    except SoftTimeLimitExceeded:
        # Propagate the term event up the chain to actually kill the worker
        task.handler.process_message("[STDERR]Operation timed out")
        task.on_term()

        if is_test:
            task.on_failure()
            task.after_return()

        raise

    if is_test:
        task.on_success()
        task.after_return()


def _initialize_process(**kwargs: Any) -> None:
    """Initialize the octave instance.

    Function to be called when a worker process is spawned. We use this to
    opportunity to actually launch octave and execute a quick MATL program
    """
    global octave

    octave = OctaveSession(octaverc=config.OCTAVERC, paths=[config.MATL_WRAP_DIR])


# When a worker process is spawned, initialize octave
worker_process_init.connect(_initialize_process)
