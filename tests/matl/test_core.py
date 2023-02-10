"""Unit tests for module for interacting with octave / MATL."""

import base64
import json
import os
import pathlib
import shutil
from datetime import datetime
from unittest.mock import Mock

import pytest
from dateutil import parser as date_parser
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pytest_mock.plugin import MockerFixture

from matl_online import matl
from matl_online.public.models import Release
from matl_online.types import MATLRunTaskParameters

TEST_DATA_DIR = pathlib.Path(os.path.dirname(__file__)).joinpath("../data")


class TestReleaseRefresh:
    """Tests for updating our local release database from GitHub."""

    def test_all_new(self, mocker: MockerFixture, app: Flask, db: SQLAlchemy) -> None:
        """Completely populate the database (no previous entries)."""
        get = mocker.patch("matl_online.matl.core.requests.get")

        with open(TEST_DATA_DIR.joinpath("releases.json")) as fid:
            data = json.load(fid)
            get.return_value.json = lambda: data

        matl.refresh_releases()

        # Now query all releases
        releases = Release.query.all()

        assert len(releases) == len(data)

        for k, release in enumerate(releases):
            assert release.tag == data[k]["tag_name"]

    def test_prerelease(
        self,
        mocker: MockerFixture,
        app: Flask,
        db: SQLAlchemy,
    ) -> None:
        """Ensure that pre-releases are ignored."""
        # Change one of the releases to a pre-release and hope it's ignored
        get = mocker.patch("matl_online.matl.core.requests.get")

        with open(TEST_DATA_DIR.joinpath("releases.json")) as fid:
            data = json.load(fid)
            data[-1]["prerelease"] = True
            get.return_value.json = lambda: data

        matl.refresh_releases()

        # Query all releases
        releases = Release.query.all()

        assert len(releases) == len(data) - 1

        for k, release in enumerate(releases):
            assert release.tag == data[k]["tag_name"]

    def test_updated_release(
        self,
        mocker: MockerFixture,
        app: Flask,
        db: SQLAlchemy,
    ) -> None:
        """Updated releases should be updated in our database."""
        get = mocker.patch("matl_online.matl.core.requests.get")

        with open(TEST_DATA_DIR.joinpath("releases.json")) as fid:
            data = json.load(fid)

            # Make a release with the first one listed here but set the
            # date to be wrong

            tag_of_interest = data[0]["tag_name"]

            Release.create(
                date=date_parser.parse(data[0]["published_at"]),
                tag=tag_of_interest,
            )

            # Now make the pub date something else
            new_date = datetime(2000, 1, 1)
            data[0]["published_at"] = new_date.isoformat()

            get.return_value.json = lambda: data

        assert Release.query.count() == 1

        matl.refresh_releases()

        releases = Release.query.all()

        assert len(releases) == len(data)

        # Now check to make sure that the release has the updated date
        updated = Release.query.filter(Release.tag == tag_of_interest).one()

        assert updated.date == new_date

    def test_updated_release_with_source(
        self,
        mocker: MockerFixture,
        app: Flask,
        db: SQLAlchemy,
        tmp_path: pathlib.Path,
    ) -> None:
        """Updated releases should remove the old source code."""
        matl_folder = mocker.patch("matl_online.matl.core.get_matl_folder")
        matl_folder.return_value = tmp_path

        assert tmp_path.is_dir()

        self.test_updated_release(mocker, app, db)

        assert not tmp_path.is_dir()


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

        matl.matl(
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

        matl.matl(
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

        matl.matl(
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

        matl.matl(
            octave_mock,
            MATLRunTaskParameters(code="'abc'", version=""),
            directory=tmp_path,
        )

        octave_mock.run.assert_called_once_with(
            "matl_runner", '"-or"', "{\"'abc'\"}", line_handler=None
        )
