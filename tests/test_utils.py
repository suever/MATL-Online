"""Unit tests for utils module."""

import pathlib
import shutil
from io import BytesIO

import pytest
from flask_sqlalchemy import SQLAlchemy
from pytest_mock.plugin import MockerFixture

from matl_online.errors import InvalidVersion
from matl_online.utils import sanitize_version, unzip

from .factories import ReleaseFactory
from .mocks import MockZipFile


class TestUnzip:
    """Test unzip functionality."""

    def test_unzip_and_flatten(
        self,
        mocker: MockerFixture,
        tmp_path: pathlib.Path,
    ) -> None:
        """Check that flattening of parent directories works as expected."""
        mock_zip = MockZipFile()
        mock_zip.add_files("my_dir/abcde", "my_dir/funky")

        zipfile = mocker.patch("matl_online.utils.zipfile.ZipFile")
        zipfile.return_value = mock_zip

        unzip(BytesIO(), tmp_path)

        extract_args = mock_zip.extract_all_arguments

        assert len(extract_args) == 2
        assert extract_args[0] == tmp_path

        output_names = [obj.filename for obj in extract_args[1]]

        assert len(output_names) == 2
        assert output_names[0] == "abcde"
        assert output_names[1] == "funky"

    def test_unzip_without_flatten(
        self,
        mocker: MockerFixture,
        tmp_path: pathlib.Path,
    ) -> None:
        """Check that unzipping (without flattening) works."""
        mock_zip = MockZipFile()
        mock_zip.add_files("my_dir/abcde", "my_dir/funky")

        zipfile = mocker.patch("matl_online.utils.zipfile.ZipFile")
        zipfile.return_value = mock_zip

        unzip(BytesIO(), tmp_path, flatten=False)

        extract_args = mock_zip.extract_all_arguments

        assert len(extract_args) == 1
        assert extract_args[0] == tmp_path

    def test_non_existent_dir(
        self,
        mocker: MockerFixture,
        tmp_path: pathlib.Path,
    ) -> None:
        """If destination doesn't exist, make sure it's created."""
        subdirectory = tmp_path.joinpath("sub")
        subdirectory.mkdir()

        shutil.rmtree(subdirectory)

        mock_zip = MockZipFile()
        mock_zip.add_files("my_directory/abcde", "my_directory/funky")

        zipfile = mocker.patch("matl_online.utils.zipfile.ZipFile")
        zipfile.return_value = mock_zip

        assert not subdirectory.is_dir()

        unzip(BytesIO(), subdirectory)

        extract_args = mock_zip.extract_all_arguments

        assert subdirectory.is_dir()
        assert extract_args[0] == subdirectory


class TestSanitizeVersion:
    def test_commit_hash_short(self) -> None:
        assert sanitize_version("abcdef12") == "abcdef12"

    def test_commit_hash_uppercase(self) -> None:
        assert sanitize_version("12ABCDEF") == "12abcdef"

    def test_hash_too_short(self) -> None:
        with pytest.raises(InvalidVersion):
            sanitize_version("ABC")

    def test_hash_truncation(self) -> None:
        assert sanitize_version("abcdef1234567890") == "abcdef12"

    def test_invalid(self, db: SQLAlchemy) -> None:
        with pytest.raises(InvalidVersion):
            sanitize_version("invalid")

    def test_version_tag(self, db: SQLAlchemy) -> None:
        # Create the version in the database
        tag = "v1.2.3.4"
        release = ReleaseFactory.build(tag=tag)
        release.save()
        assert sanitize_version(tag) == tag

    def test_missing_version_tag(self, db: SQLAlchemy) -> None:
        tag = "v1.2.3.4"
        release = ReleaseFactory.build(tag=tag + ".5")
        release.save()

        with pytest.raises(InvalidVersion):
            sanitize_version(tag)
