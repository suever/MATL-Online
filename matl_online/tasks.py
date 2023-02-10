"""Celery tasks for running MATL programs."""
from __future__ import annotations

import logging
import pathlib
import tempfile
from functools import cached_property
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
from matl_online.types import MATLTaskParameters

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

        if message == "[CLC]":
            self.send()
            self.clear()
            return

        if message.startswith("warning:"):
            return

        if message.startswith("MATL run-time error:"):
            for item in message.split("\n"):
                self.contents.append("[STDERR]" + item)

            return

        self.contents.append(message)


class OctaveTask(Task[[MATLTaskParameters], None]):
    """Custom Task type for interacting with octave."""

    abstract: bool = True
    session_id: Optional[str] = None

    throws = (SoftTimeLimitExceeded,)

    @property
    def octave(self) -> Optional[OctaveSession]:
        """Dependent property which automatically spawns octave if needed."""
        global octave
        return octave

    @cached_property
    def handler(self) -> OutputHandler:
        """Dependent property that creates an OutputHandler instance."""
        return OutputHandler(self)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """Send an event to any listening clients."""
        socket.emit(*args, room=self.session_id, **kwargs)

    def on_term(self) -> None:
        """Clean up after termination event."""
        # Restart octave, so we're ready to go with future calls
        if self.octave:
            self.octave.restart()

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

    def send_results(self) -> Dict[str, Any]:
        """Local forwarder for all send events."""
        return self.handler.send()

    def on_failure(self, *args: Any, **kwargs: Any) -> None:
        """Send a message if the task failed for any reason."""
        self.send_results()
        self.emit("complete", {"success": False})


@celery.task(base=OctaveTask, bind=True)
def matl_task(
    task: OctaveTask,
    params: MATLTaskParameters,
) -> Dict[str, Any]:
    """Celery task for processing a MATL command and returning the result."""
    task.session_id = params.session_id
    task.handler.clear()

    assert task.octave, "Octave is not configured properly"

    with tempfile.TemporaryDirectory() as folder:
        try:
            matl(
                task.octave,
                params,
                directory=pathlib.Path(folder),
                line_handler=task.handler.process_message,
            )

            result = task.send_results()

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
            raise

    return result


def _initialize_process(**kwargs: Any) -> None:
    """Initialize the octave instance.

    Function to be called when a worker process is spawned. We use this to
    opportunity to actually launch octave and execute a quick MATL program
    """

    # Create a global reference to octave that is unique to this worker process
    global octave

    octave = OctaveSession(
        octaverc=config.OCTAVERC,
        default_paths=[
            config.MATL_WRAP_DIR,
        ],
        logger=logging.Logger(__name__),
    )


# When a worker process is spawned, initialize octave
worker_process_init.connect(_initialize_process)
