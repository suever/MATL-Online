"""Unit tests for module for interacting with octave / MATL."""

import pathlib
from unittest.mock import Mock

from flask import Flask
from pytest_mock.plugin import MockerFixture

from matl_online.matl.core import matl
from matl_online.types import MATLRunTaskParameters


class TestMATLInterface:
    """Some basic tests to check that the MATL interface is working."""

    def test_empty_inputs(
        self,
        mocker: MockerFixture,
        app: Flask,
        octave_mock: Mock,
        tmp_path: pathlib.Path,
    ) -> None:
        """If no inputs are provided, MATL shouldn't receive any."""
        get_matl_folder = mocker.patch("matl_online.matl.core.get_matl_folder")
        matl_folder = pathlib.Path("matl_folder")
        get_matl_folder.return_value = pathlib.Path(matl_folder)

        matl(
            octave_mock,
            MATLRunTaskParameters(code="", version=""),
            directory=tmp_path,
        )

        # Ensure we use the temporary folder
        assert octave_mock.current_directory.called_once_with(tmp_path)

        # Ensure we added the MATL code directory to the path
        assert octave_mock.paths.called_once_with(matl_folder)

    def test_single_input(
        self,
        mocker: MockerFixture,
        app: Flask,
        octave_mock: Mock,
        tmp_path: pathlib.Path,
    ) -> None:
        """Single input parameter should be send to matl_runner."""
        get_matl_folder = mocker.patch("matl_online.matl.core.get_matl_folder")
        get_matl_folder.return_value = pathlib.Path("")

        matl(
            octave_mock,
            MATLRunTaskParameters(code="D", inputs="12", version=""),
            directory=tmp_path,
        )

        octave_mock.run.assert_called_once_with(
            "matl_runner", '"-or"', '{"D"}', '"12"', line_handler=None
        )

    def test_multiple_inputs(
        self,
        mocker: MockerFixture,
        app: Flask,
        octave_mock: Mock,
        tmp_path: pathlib.Path,
    ) -> None:
        """Multiple input parameters should be sent to matl_runner."""
        get_matl_folder = mocker.patch("matl_online.matl.core.get_matl_folder")
        get_matl_folder.return_value = pathlib.Path("")

        matl(
            octave_mock,
            MATLRunTaskParameters(code="D", inputs="12\n13", version=""),
            directory=tmp_path,
        )

        octave_mock.run.assert_called_once_with(
            "matl_runner", '"-or"', '{"D"}', '"12"', '"13"', line_handler=None
        )

    def test_string_escape(
        self,
        mocker: MockerFixture,
        app: Flask,
        octave_mock: Mock,
        tmp_path: pathlib.Path,
    ) -> None:
        """All single quotes need to be escaped properly."""
        get_matl_folder = mocker.patch("matl_online.matl.core.get_matl_folder")
        get_matl_folder.return_value = pathlib.Path("")

        matl(
            octave_mock,
            MATLRunTaskParameters(code="'abc'", version=""),
            directory=tmp_path,
        )

        octave_mock.run.assert_called_once_with(
            "matl_runner", '"-or"', "{\"'abc'\"}", line_handler=None
        )
