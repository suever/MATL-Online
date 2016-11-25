"""Module for creating an octave instance."""

from oct2py import Oct2Py

from matl_online.settings import Config

# Initialize an octave session with the desired executable
octave = Oct2Py(Config.OCTAVE_EXECUTABLE,
                timeout=Config.CELERYD_TASK_TIME_LIMIT)
