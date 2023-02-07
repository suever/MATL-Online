"""Module for creating an octave instance."""
import os
from typing import Optional

from octave_kernel.kernel import OctaveEngine

from matl_online.settings import Config

# Set the environment variable to specify additional command-line input
# arguments to Octave
os.environ["OCTAVE_CLI_OPTIONS"] = Config.OCTAVE_CLI_OPTIONS
os.environ["OCTAVE_EXECUTABLE"] = Config.OCTAVE_EXECUTABLE


# Initialize an octave session with the desired executable
class OctaveSession:
    """Class for communicating with Octave."""

    _engine: Optional[OctaveEngine]

    def __init__(self, octaverc=None, paths=None):
        """Build the Octave interface with the specified config and PATH."""
        self.octaverc = octaverc
        self.paths = paths if paths else []
        self.launch()

    def launch(self):
        """Launch Octave and execute setup commands."""
        self._engine = OctaveEngine()

        if self.octaverc:
            self.eval('source("' "%s" '")' % self.octaverc)

        for path in self.paths:
            self.eval('addpath("' "%s" '")' % path)

    def eval(self, code, **kwargs):
        """Evaluate some code in Octave."""
        handler = kwargs.pop("line_handler", self._engine.line_handler)
        self._engine.line_handler = handler
        return self._engine.eval(code, **kwargs)

    def restart(self):
        """Terminate and re-launch the Octave instance."""
        if self._engine:
            self.terminate()

        self.launch()

    def terminate_repl(self):
        """Terminate the REPL but keep the handle around"""
        self._engine.repl.terminate()

    def terminate(self):
        """Terminate the underlying Octave process."""
        self.terminate_repl()
        self._engine = None
