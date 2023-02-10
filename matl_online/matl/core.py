"""Module for interacting with MATL, and it's source code."""
import pathlib
from typing import Optional

from matl_online.octave import OctaveSession, OutputCallback
from matl_online.octave import string as octave_string
from matl_online.types import MATLTaskParameters

from .source import get_matl_folder


def matl(
    octave: OctaveSession,
    matl_params: MATLTaskParameters,
    directory: pathlib.Path,
    line_handler: Optional[OutputCallback] = None,
) -> None:
    """Open a session with Octave and manages input/output as well as errors."""

    # Add the folder for the appropriate MATL version
    matl_folder = get_matl_folder(matl_params.version)

    # Ensure the matl folder exists
    assert matl_folder, "MATL folder does not exist"

    # Change directories to the temporary folder so that all temporary
    # files are placed in here and won't interfere with other requests
    with octave.current_directory(directory):
        with octave.paths(matl_folder):
            # Convert the code to a cell array element-per-line
            code = f"{{{','.join([octave_string(x) for x in matl_params.code_lines])}}}"

            octave.run(
                "matl_runner",
                octave_string(matl_params.flags),
                code,
                *[octave_string(x) for x in matl_params.input_lines],
                line_handler=line_handler,
            )
