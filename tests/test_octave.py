"""Unit tests for the module for interacting with Octave."""

import pathlib
from typing import Any, List

from pytest_mock.plugin import MockerFixture

from matl_online.octave import OctaveSession, string


class TestOctaveSession:
    """Series of tests for the OctaveSession class."""

    def test_no_inputs(self, mocker: MockerFixture) -> None:
        """Ensure the proper default parameters."""
        # Make sure that eval wasn't called
        octave = mocker.patch("matl_online.octave.OctaveSession.eval")

        session = OctaveSession()

        assert session.octaverc is None
        assert session.default_paths == []

        octave.assert_not_called()

    def test_octaverc(self, mocker: MockerFixture) -> None:
        """Ensure that the octaverc file is sourced."""
        octaverc = pathlib.Path("path/to/my/.octaverc")

        run = mocker.patch("matl_online.octave.OctaveSession.run")

        session = OctaveSession(octaverc=octaverc)

        assert session.octaverc == octaverc
        assert session.default_paths == []

        run.assert_called_once_with("source", '"path/to/my/.octaverc"')

    def test_default_paths(self, mocker: MockerFixture) -> None:
        """Ensure that the specified default paths are added to the path."""
        paths = [
            pathlib.Path("path1"),
            pathlib.Path("path2"),
            pathlib.Path("path3"),
        ]

        run = mocker.patch("matl_online.octave.OctaveSession.run")

        session = OctaveSession(default_paths=paths)

        assert session.octaverc is None
        assert session.default_paths == paths

        run.assert_called_once_with("addpath", '"path1"', '"path2"', '"path3"')

    def test_eval_without_handler(self, mocker: MockerFixture) -> None:
        """Ensure that code is sent to octave for evaluation."""
        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")

        session = OctaveSession()
        code = "1 + 1"
        session.eval(code)

        octave.assert_called_with(code)

    def test_eval_with_handler(self, mocker: MockerFixture) -> None:
        """Ensure that the stream handler is used."""
        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")

        session = OctaveSession()
        code = "1 + 1"

        output_list: List[str] = list()
        handler = output_list.append

        session.eval(code, line_handler=handler)

        assert session._engine

        assert session._engine.line_handler == handler
        octave.assert_called_with(code)

    def test_terminate(self) -> None:
        """Ensure that we stop the Octave instance."""
        session = OctaveSession()

        assert session._engine is not None

        session.terminate()

        assert session._engine is None

    def test_restart(self) -> None:
        """Make sure we stop and restart the octave instance."""
        session = OctaveSession()

        engine1 = session._engine

        session.restart()

        assert session._engine is not None
        assert session._engine != engine1

    def test_run_no_arguments(self, mocker: MockerFixture) -> None:
        """Ensure that we evaluate commands as expected."""
        session = OctaveSession()

        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")
        octave.return_value = "return_value"

        output = session.run("cd")

        octave.assert_called_with("cd();\n")

        assert output == "return_value"

    def test_run_arguments(self, mocker: MockerFixture) -> None:
        """Ensure that we evaluate commands as expected."""
        session = OctaveSession()

        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")

        # First argument is a non-string literal and the second is a string literal that needs to be escaped
        session.run("cat", "[1,2,3]", '"4"')

        octave.assert_called_with('cat([1,2,3],"4");\n')

    def test_cd(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        """Ensure that we issue the command to change directories."""
        session = OctaveSession()

        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")

        session.cd(tmp_path)

        octave.assert_called_with(f'cd("{tmp_path.as_posix()}");\n')

    def test_pwd(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        """Ensure that we retrieve the current working directory."""
        session = OctaveSession()

        def eval_result(*args: Any) -> str:
            assert args == ("disp(pwd);\n",)
            return tmp_path.as_posix() + "\r\n"

        mocker.patch(
            "matl_online.octave.OctaveEngine.eval",
            side_effect=eval_result,
        )

        assert session.pwd() == tmp_path

    def test_current_directory(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        """Ensure we change directories but then revert them back when we're done."""
        session = OctaveSession()

        original_directory = pathlib.Path("/starting/directory")

        mocker.patch(
            "matl_online.octave.OctaveSession.pwd",
            return_value=original_directory,
        )

        octave = mocker.patch("matl_online.octave.OctaveEngine.eval")

        with session.current_directory(tmp_path):
            # Ensure we have switched to this temporary directory
            octave.assert_called_once_with(f'cd("{tmp_path.as_posix()}");\n')

            # Reset the mock so we can register additional calls
            octave.reset_mock()

        octave.assert_called_once_with(f'cd("{original_directory.as_posix()}");\n')

    def test_paths(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        """Ensure that we add the specified directory to the path but then remove it."""
        session = OctaveSession()

        run_mock = mocker.patch("matl_online.octave.OctaveSession.run")

        with session.paths(tmp_path):
            run_mock.assert_called_once_with("addpath", f'"{tmp_path.as_posix()}"')
            run_mock.reset_mock()

        run_mock.assert_called_once_with("rmpath", f'"{tmp_path.as_posix()}"')

    def test_no_paths(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        """Ensure there are no issues when no path modifications are made."""
        session = OctaveSession()

        run_mock = mocker.patch("matl_online.octave.OctaveSession.run")

        with session.paths():
            run_mock.assert_not_called()

        run_mock.assert_not_called()


class TestString:
    def test_double_quotes(self) -> None:
        """Ensure double quotes are properly escaped."""
        original = 'testing "quotes"'

        assert string(original) == '"testing \\"quotes\\""'

    def test_backslackes(self) -> None:
        """Ensure backslashes are properly escaped."""
        original = "testing \\backslashes\\"

        assert string(original) == r'"testing \\backslashes\\"'
