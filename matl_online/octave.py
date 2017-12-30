"""Module for creating an octave instance."""
import os

from oct2py import Oct2Py

from matl_online.settings import Config

# Set the environment variable to specify additional command-line input
# arguments to Octave
os.environ['OCTAVE_CLI_OPTIONS'] = Config.OCTAVE_CLI_OPTIONS

# Initialize an octave session with the desired executable
octave = Oct2Py(Config.OCTAVE_EXECUTABLE,
                timeout=Config.CELERYD_TASK_TIME_LIMIT)
