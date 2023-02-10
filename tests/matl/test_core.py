"""Unit tests for module for interacting with octave / MATL."""

import base64
import json
import os
import pathlib
import shutil
from datetime import datetime
from unittest.mock import Mock

import pytest
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pytest_mock.plugin import MockerFixture

from matl_online import matl
from matl_online.public.models import Release
from matl_online.types import MATLRunTaskParameters
from tests.factories import DocumentationLinkFactory as DocLink

TEST_DATA_DIR = pathlib.Path(os.path.dirname(__file__)).joinpath("../data")


class TestSourceCache:
    """Series of tests to check if source code is managed properly."""

    def test_no_source_no_install(self, app: Flask, tmp_path: pathlib.Path) -> None:
        """The source folder does not exist, and we won't create it."""
        app.config["MATL_FOLDER"] = tmp_path.as_posix()
        folder = matl.get_matl_folder("18.3.0", install=False)

        # In this case, the result should simply be None
        assert folder is None

    def test_no_source_install(
        self,
        app: Flask,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
    ) -> None:
        """The source folder does not exist, but we'll fetch the source."""
        mock_install = mocker.patch("matl_online.matl.core.install_matl")
        app.config["MATL_FOLDER"] = tmp_path.as_posix()

        version = "0.0.0"

        folder = matl.get_matl_folder(version)
        expected = tmp_path.joinpath(version)

        mock_install.assert_called_once_with(version, expected)
        assert folder == expected

    def test_source_folder_exists(self, app: Flask, tmp_path: pathlib.Path) -> None:
        """Source folder exists so simply return it."""
        app.config["MATL_FOLDER"] = tmp_path.as_posix()

        # Create the source folder
        version = "13.4.0"

        version_directory = tmp_path.joinpath(version)
        version_directory.mkdir()
        folder = matl.get_matl_folder(version, install=False)

        # Make sure that we only return the source folder
        assert folder == version_directory


class TestDocLinks:
    """Ensure that documentation hyperlinks are added appropriately."""

    def test_basic_doclink(self, db: SQLAlchemy) -> None:
        """Use a straightforward single function name."""
        link: DocLink = DocLink(name="ans")
        template = "This is a doc string for <strong>%s</strong>"

        output = matl.add_doc_links(template % link.name)

        soup = BeautifulSoup(output, "html.parser")

        assert soup.strong and soup.strong.a

        assert soup.strong.a["href"] == link.link
        assert soup.strong.a.text == link.name

    def test_multiple_doclink(self, db: SQLAlchemy) -> None:
        """Include two functions in the same docstring."""
        links = (DocLink(name="func1"), DocLink(name="func2"))
        template = "This is a doc for <strong>%s</strong>"

        docstring = (template % links[0].name) + (template % links[1].name)

        output = matl.add_doc_links(docstring)

        soup = BeautifulSoup(output, "html.parser")

        strong_tags = soup.findAll("strong")

        assert len(strong_tags) == len(links)

        for k, strong in enumerate(strong_tags):
            assert strong.a["href"] == links[k].link
            assert strong.a.text == links[k].name

    def test_single_quoted(self, db: SQLAlchemy) -> None:
        """Single quoted function names should be ignored."""
        double: DocLink = DocLink(name="double")
        links = (DocLink(name="func1"), DocLink(name="func2"))

        docstring = (
            "doc string for <strong>'%s'</strong>, "
            "<strong>%s</strong> and <strong>%s</strong>"
        ) % (double.name, links[0].name, links[1].name)

        output = matl.add_doc_links(docstring)

        soup = BeautifulSoup(output, "html.parser")
        strong_tags = soup.findAll("strong")

        # Make sure the first one wasn't converted to a link
        first_tag = strong_tags.pop(0)
        assert first_tag.a is None

        # Make sure everything else is golden
        assert len(strong_tags) == len(links)

        for k, strong in enumerate(strong_tags):
            assert strong.a["href"] == links[k].link
            assert strong.a.text == links[k].name

    def test_complex_function(self, db: SQLAlchemy) -> None:
        """Test when there is a multi-function example."""
        mat2cell: DocLink = DocLink(name="mat2cell")
        ones = DocLink(name="ones")
        size = DocLink(name="size")
        ndims = DocLink(name="ndims")

        expected = [mat2cell, ones, size, size, size, ndims]

        ex = "mat2cell(x, ones(size(x,1),1), size(x,2),...,size(x,ndims(x)))"
        docstring = "Doc for: <strong>%s</strong>" % ex

        output = matl.add_doc_links(docstring)

        soup = BeautifulSoup(output, "html.parser")

        assert len(soup.findAll("strong")) == 1

        assert soup.strong

        links = soup.strong.findAll("a")

        assert len(links) == len(expected)

        for k, link in enumerate(links):
            assert link.text == expected[k].name
            assert link["href"] == expected[k].link


class TestResults:
    """Series of tests to ensure proper MATL output parsing."""

    def test_error_parsing(self) -> None:
        """All errors are correctly classified."""
        msg = "single error"
        result = matl.parse_matl_results("[STDERR]" + msg)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stderr"
        assert result[0]["value"] == msg

    def test_invalid_image_parsing(self) -> None:
        """Test with a bad filename and ensure no result."""
        filename = "/ignore/this/filename.png"
        result = matl.parse_matl_results("[IMAGE]" + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_nn_image_parsing(self, tmp_path: pathlib.Path) -> None:
        """Test for nearest-neighbor interpolated image."""
        file_handle = tmp_path.joinpath("image.png")
        contents = b"hello"

        with open(file_handle, "wb") as fid:
            fid.write(contents)

        # Parse the string
        result = matl.parse_matl_results("[IMAGE_NN]" + file_handle.as_posix())

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "image_nn"

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents).decode()
        assert result[0]["value"] == "data:image/png;base64," + encoded

        # Make sure the file was not removed
        assert file_handle.is_file()

    def test_image_parsing(self, tmp_path: pathlib.Path) -> None:
        """Test valid image result."""
        file_handle = tmp_path.joinpath("image.png")
        contents = b"hello"

        with open(file_handle, "wb") as fid:
            fid.write(contents)

        # Parse the string
        result = matl.parse_matl_results("[IMAGE]" + file_handle.as_posix())

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "image"

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents).decode()
        assert result[0]["value"] == "data:image/png;base64," + encoded

        # Make sure the file was not removed
        assert file_handle.is_file()

    def test_invalid_audio_parsing(self) -> None:
        """Test with a bad filename and ensure no result."""
        filename = "/ignore/this/audio.wav"
        result = matl.parse_matl_results("[AUDIO]" + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_audio_parsing(self, tmp_path: pathlib.Path) -> None:
        """Test valid audio result."""
        file_handle = tmp_path.joinpath("audio.wav")
        contents = b"AUDIO"

        with open(file_handle, "wb") as fid:
            fid.write(contents)

        # Parse the string
        result = matl.parse_matl_results("[AUDIO]" + file_handle.as_posix())

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "audio"

        encoded = base64.b64encode(contents).decode()
        assert result[0]["value"] == "data:audio/wav;base64," + encoded

        # Make sure that the file was not removed
        assert file_handle.is_file()

    def test_stdout2_parsing(self) -> None:
        """Test potential to have a second type of STDOUT."""
        expected = "ouptut2"
        result = matl.parse_matl_results("[STDOUT]" + expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stdout2"
        assert result[0]["value"] == expected

    def test_stdout_single_line_parsing(self) -> None:
        """A single line of output is handled as STDOUT."""
        expected = "standard output"
        result = matl.parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stdout"
        assert result[0]["value"] == expected

    def test_stdout_multi_line_parsing(self) -> None:
        """Multi-line output is also handled as STDOUT if not specified."""
        expected = "standard\noutput"
        result = matl.parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stdout"
        assert result[0]["value"] == expected


class TestHelpParsing:
    """Series of tests for checking help to JSON conversion."""

    def test_generate_help_json(
        self,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
        db: SQLAlchemy,
    ) -> None:
        """Check all reading / parsing of help .mat file."""
        folder = mocker.patch("matl_online.matl.core.get_matl_folder")
        folder.return_value = tmp_path

        # Copy the test file into place
        shutil.copy(
            os.path.join(TEST_DATA_DIR, "help.mat"),
            tmp_path.joinpath("help.mat"),
        )

        outfile = matl.help_file("1.2.3")

        assert outfile == folder.return_value.joinpath("help.json")

        # Now actually check the file
        with open(outfile, "r") as fid:
            data = json.load(fid)

        assert "data" in data
        assert len(data["data"]) == 3

        # Make sure it has all the necessary keys
        expected = ["source", "description", "brief", "arguments"]
        expected.sort()

        actual = list(data["data"][0].keys())
        actual.sort()

        assert actual == expected

        item = data["data"][0]

        # make sure all newlines were removed from description
        assert item.get("description").find("\n") == -1
        assert item.get("arguments") == ""
        assert item.get("source") == "&amp;"
        assert item.get("brief") == "alternative input/output specification"

        item = data["data"][1]

        assert item.get("description").find("\n") == -1
        assert item.get("arguments") == "1--2 (1 / 2);  1"
        assert item.get("source") == "a"
        assert item.get("brief") == "any"

        item = data["data"][2]

        assert item.get("description") == "    "
        assert item.get("arguments") == "0;  1"
        assert item.get("source") == "Y?"
        assert item.get("brief") == ""

    def test_help_json_exists(
        self,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
    ) -> None:
        """Verify correctness of output JSON."""
        folder = mocker.patch("matl_online.matl.core.get_matl_folder")
        folder.return_value = tmp_path

        json_file = tmp_path.joinpath("help.json")
        contents = "placeholder"

        with open(json_file, "w") as fid:
            fid.write(contents)

        outfile = matl.help_file("1.2.3")

        assert outfile == json_file

        # Make sure the file wasn't updated
        with open(outfile, "r") as fid:
            assert fid.read() == contents


class TestInstall:
    """Tests to check if MATL is properly downloaded and installed."""

    def test_valid_version(
        self,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
        app: Flask,
    ) -> None:
        """Test using a version which we know to exist on GitHub."""
        get = mocker.patch("matl_online.matl.core.requests.get")
        get.return_value.status_code = 200
        get.return_value.json = lambda: {"zipball_url": "zipball"}
        content = b"zipball_content"
        get.return_value.content = content

        zipper = mocker.patch("matl_online.matl.core.unzip")

        matl.install_matl("1.2.3", tmp_path)

        assert zipper.called
        assert zipper.call_args[0][0].read() == content
        assert zipper.call_args[0][1] == tmp_path

    def test_invalid_version(
        self,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
        app: Flask,
    ) -> None:
        """Try to install a version which does NOT exist on GitHub."""
        get = mocker.patch("matl_online.matl.requests.get")
        get.return_value.status_code = 404

        with pytest.raises(KeyError):
            matl.install_matl("3.4.5", tmp_path)


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
