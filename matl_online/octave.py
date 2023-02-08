"""Module for creating an octave instance."""
import os
import pathlib
from typing import Any, Callable, Dict, List, Optional, Union

from octave_kernel.kernel import OctaveEngine  # type: ignore

from matl_online.settings import Config

# Set the environment variable to specify additional command-line input
# arguments to Octave
os.environ["OCTAVE_CLI_OPTIONS"] = Config.OCTAVE_CLI_OPTIONS
os.environ["OCTAVE_EXECUTABLE"] = Config.OCTAVE_EXECUTABLE


# Initialize an octave session with the desired executable
class OctaveSession:
    """Class for communicating with Octave."""

    _engine: Optional[OctaveEngine]

    def __init__(
        self,
        octaverc: Optional[Union[str, pathlib.Path]] = None,
        paths: Optional[List[str]] = None,
    ) -> None:
        """Build the Octave interface with the specified config and PATH."""
        self.octaverc = octaverc
        self.paths = paths if paths else []
        self.launch()

    def launch(self) -> None:
        """Launch Octave and execute setup commands."""
        self._engine = OctaveEngine()

        if self.octaverc:
            self.eval('source("' "%s" '")' % self.octaverc)

        for path in self.paths:
            self.eval('addpath("' "%s" '")' % path)

    def eval(
        self,
        code: str,
        line_handler: Optional[Callable[[str], None]] = None,
        **kwargs: Dict[str, Any],
    ) -> Any:
        """Evaluate some code in Octave."""

        if self._engine is None:
            raise Exception("Engine not defined")

        if line_handler:
            self._engine.line_handler = line_handler

        return self._engine.eval(code, **kwargs)

    def restart(self) -> None:
        """Terminate and re-launch the Octave instance."""
        if self._engine:
            self.terminate()

        self.launch()

    def terminate_repl(self) -> None:
        """Terminate the REPL but keep the handle around"""
        self._engine and self._engine.repl.terminate()

    def terminate(self) -> None:
        """Terminate the underlying Octave process."""
        self.terminate_repl()
        self._engine = None
