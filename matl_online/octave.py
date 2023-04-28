"""Module for creating an octave instance."""
import logging
import os
import pathlib
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional

from octave_kernel.kernel import OctaveEngine  # type: ignore

from matl_online.settings import Config

# Set the environment variable to specify additional command-line input
# arguments to Octave
os.environ["OCTAVE_CLI_OPTIONS"] = Config.OCTAVE_CLI_OPTIONS
os.environ["OCTAVE_EXECUTABLE"] = Config.OCTAVE_EXECUTABLE

OutputCallback = Callable[[str], None]


def string(value: str) -> str:
    # Takes the input and ensure it is wrapped in double quotes and then all
    # necessary characters are escaped
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


class OctaveSession:
    """Class for communicating with Octave."""

    _engine: Optional[OctaveEngine]
    default_paths: List[pathlib.Path]
    octaverc: Optional[pathlib.Path]
    logger: logging.Logger

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        octaverc: Optional[pathlib.Path] = None,
        default_paths: Optional[List[pathlib.Path]] = None,
    ) -> None:
        """Build the Octave interface with the specified config and PATH."""
        self.octaverc = octaverc
        self.default_paths = default_paths if default_paths else []

        self.logger = logger or logging.Logger(__name__)

        self.launch()

    def launch(self) -> None:
        """Launch Octave and execute setup commands."""
        self._engine = OctaveEngine()

        if self.octaverc:
            self.run("source", string(self.octaverc.as_posix()))

        self.add_paths(*self.default_paths)

    def add_paths(self, *paths: pathlib.Path) -> str:
        path_strings = [string(path.as_posix()) for path in paths]

        if len(paths) == 0:
            return ""

        return self.run("addpath", *path_strings)

    def remove_paths(self, *paths: pathlib.Path) -> str:
        path_strings = [string(path.as_posix()) for path in paths]

        if len(paths) == 0:
            return ""

        return self.run("rmpath", *path_strings)

    @contextmanager
    def paths(self, *paths: pathlib.Path) -> Generator[None, None, None]:
        self.add_paths(*paths)

        yield

        self.remove_paths(*paths)

    @contextmanager
    def current_directory(self, directory: pathlib.Path) -> Generator[None, None, None]:
        """Allow the caller to execute"""
        # Get the original directory
        original_directory = self.pwd()

        self.cd(directory)

        yield

        self.cd(original_directory)

    def pwd(self) -> pathlib.Path:
        return pathlib.Path(self.run("disp", "pwd").rstrip()).absolute()

    def cd(self, path: pathlib.Path) -> None:
        self.run("cd", string(path.as_posix()))

    def run(
        self,
        command: str,
        *args: str,
        line_handler: Optional[OutputCallback] = None,
    ) -> str:
        command_string = f"{command}({','.join(args)});\n"
        self.logger.info(command_string)
        return self.eval(command_string, line_handler=line_handler)

    def eval(
        self,
        code: str,
        line_handler: Optional[OutputCallback] = None,
        **kwargs: Dict[str, Any],
    ) -> str:
        """Evaluate some code in Octave."""

        assert self._engine, "Engine is not defined"

        self._engine.line_handler = line_handler

        output: str = self._engine.eval(code, **kwargs)
        return output

    def restart(self) -> None:
        """Terminate and re-launch the Octave instance."""
        self.terminate()
        self.launch()

    def terminate_repl(self) -> None:
        """Terminate the REPL but keep the handle around"""
        self._engine and self._engine.repl.terminate()

    def terminate(self) -> None:
        """Terminate the underlying Octave process."""
        self.terminate_repl()
        self._engine = None
