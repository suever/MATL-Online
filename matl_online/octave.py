"""Module for creating an octave instance."""
import os

from octave_kernel.kernel import OctaveEngine

from matl_online.settings import Config

# Set the environment variable to specify additional command-line input
# arguments to Octave
os.environ['OCTAVE_CLI_OPTIONS'] = Config.OCTAVE_CLI_OPTIONS
os.environ['OCTAVE_EXECUTABLE'] = Config.OCTAVE_EXECUTABLE

# Initialize an octave session with the desired executable
class OctaveSession:

    def __init__(self, octaverc=None, paths=None):
        self.octaverc = octaverc
        self.paths = paths if paths else []
        self.launch()

    def launch(self):
        self._engine = OctaveEngine()

        if self.octaverc:
            self.eval('source("''%s''")' % self.octaverc)

        for path in self.paths:
            self.eval('addpath("''%s''")' % path)

    def eval(self, code, **kwargs):
        handler = kwargs.pop('stream_handler', self._engine.stream_handler)
        self._engine.stream_handler = handler
        return self._engine.eval(code, **kwargs)

    def restart(self):
        if self._engine:
            self.terminate()

        self.launch()

    def terminate(self):
        self._engine.repl.terminate()
        self._engine = None
