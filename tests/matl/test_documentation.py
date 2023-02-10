import json
import pathlib
import shutil

from flask_sqlalchemy import SQLAlchemy
from pytest_mock.plugin import MockerFixture

from matl_online.matl.documentation import help_file

TEST_DATA_DIRECTORY = pathlib.Path(__file__).parents[1].joinpath("data").absolute()


class TestHelpParsing:
    """Series of tests for checking help to JSON conversion."""

    def test_generate_help_json(
        self,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
        db: SQLAlchemy,
    ) -> None:
        """Check all reading / parsing of help .mat file."""
        folder = mocker.patch("matl_online.matl.documentation.get_matl_folder")
        folder.return_value = tmp_path

        # Copy the test file into place
        shutil.copy(
            TEST_DATA_DIRECTORY.joinpath("help.mat"),
            tmp_path.joinpath("help.mat"),
        )

        outfile = help_file("1.2.3")

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
        assert item.get("source") == "!"
        assert item.get("brief") == "transpose / permute array dimensions"

        item = data["data"][1]

        assert item.get("description").find("\n") == -1
        assert item.get("arguments") == "1--2 (2); 1"
        assert item.get("source") == "X!"
        assert item.get("brief") == "rotate array in steps of 90 degrees"

        item = data["data"][2]

        assert item.get("description") == "    <strong>system</strong> "
        assert item.get("arguments") == "1; 0--2 (2)"
        assert item.get("source") == "Y!"
        assert item.get("brief") == "execute system command"

    def test_help_json_exists(
        self,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
    ) -> None:
        """Verify correctness of output JSON."""
        folder = mocker.patch("matl_online.matl.documentation.get_matl_folder")
        folder.return_value = tmp_path

        json_file = tmp_path.joinpath("help.json")
        contents = "placeholder"

        with open(json_file, "w") as fid:
            fid.write(contents)

        outfile = help_file("1.2.3")

        assert outfile == json_file

        # Make sure the file wasn't updated
        with open(outfile, "r") as fid:
            assert fid.read() == contents
