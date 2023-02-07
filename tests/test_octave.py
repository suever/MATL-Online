"""Unit tests for the module for interacting with Octave."""

import os
from unittest import mock

from matl_online.octave import OctaveSession


class TestOctaveSession:
    """Series of tests for the OctaveSession class."""

    def test_no_inputs(self, mocker):
        """Ensure the proper default parameters."""
        # Make sure that eval wasn't called
        octave = mocker.patch("matl_online.octave.OctaveSession.eval")

        session = OctaveSession()

        assert session.octaverc is None
        assert session.paths == []

        octave.assert_not_called()

    def test_octaverc(self, mocker):
        """Ensure that the octaverc file is sourced."""
        octaverc = os.path.join("path", "to", "my", ".octaverc")

        octave = mocker.patch("matl_online.octave.OctaveSession.eval")

        session = OctaveSession(octaverc=octaverc)

        assert session.octaverc == octaverc
        assert session.paths == []

        octave.assert_called_once_with('source("' "%s" '")' % octaverc)

    def test_paths(self, mocker):
        """Ensure that the specified paths are added to the path."""
        paths = ["path1", "path2", "path3"]

        eval_mock = mocker.patch("matl_online.octave.OctaveSession.eval")

        session = OctaveSession(paths=paths)

        assert session.octaverc is None
        assert session.paths == paths

        expected_calls = [mock.call('addpath("' "%s" '")' % path) for path in paths]
        eval_mock.assert_has_calls(expected_calls)

    def test_eval_without_handler(self, mocker):
        """Ensure that code is sent to octave for evaluation."""
        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")

        session = OctaveSession()
        code = "1 + 1"
        session.eval(code)

        octave.assert_called_with(code)

    def test_eval_with_handler(self, mocker):
        """Ensure that the stream handler is used."""
        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")

        session = OctaveSession()
        code = "1 + 1"

        output_list = list()
        handler = output_list.append

        session.eval(code, line_handler=handler)

        assert session._engine.line_handler == handler
        octave.assert_called_with(code)

    def test_terminate(self):
        """Ensure that we stop the Octave instance."""
        session = OctaveSession()

        assert session._engine is not None

        session.terminate()

        assert session._engine is None

    def test_restart(self):
        """Make sure we stop and restart the octave instance."""
        session = OctaveSession()

        engine1 = session._engine

        session.restart()

        assert session._engine is not None
        assert session._engine != engine1
