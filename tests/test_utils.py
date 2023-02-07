"""Unit tests for utils module."""

import os
import shutil

from matl_online.utils import unzip

from .mocks import MockZipFile


class TestUnzip:
    """Test unzip functionality."""

    def test_unzip_and_flatten(self, mocker, tmpdir):
        """Check that flattening of parent directories works as expected."""
        mock_zip = MockZipFile()
        mock_zip.add_files("my_dir/abcde", "my_dir/funky")

        zipfile = mocker.patch("matl_online.utils.zipfile.ZipFile")
        zipfile.return_value = mock_zip

        unzip("", tmpdir.strpath)

        extract_args = mock_zip.extract_arguments

        assert len(extract_args) == 2
        assert extract_args[0] == tmpdir.strpath

        output_names = [obj.filename for obj in extract_args[1]]

        assert len(output_names) == 2
        assert output_names[0] == "abcde"
        assert output_names[1] == "funky"

    def test_unzip_without_flatten(self, mocker, tmpdir):
        """Check that unzipping (without flattening) works."""
        mock_zip = MockZipFile()
        mock_zip.add_files("my_dir/abcde", "my_dir/funky")

        zipfile = mocker.patch("matl_online.utils.zipfile.ZipFile")
        zipfile.return_value = mock_zip

        unzip("", tmpdir.strpath, flatten=False)

        extract_args = mock_zip.extract_arguments

        assert len(extract_args) == 1
        assert extract_args[0] == tmpdir.strpath

    def test_non_existent_dir(self, mocker, tmpdir):
        """If destination doesn't exist, make sure it's created."""
        subdir = tmpdir.mkdir("sub")
        sub_path = subdir.strpath
        shutil.rmtree(sub_path)

        mock_zip = MockZipFile()
        mock_zip.add_files("my_directory/abcde", "my_directory/funky")

        zipfile = mocker.patch("matl_online.utils.zipfile.ZipFile")
        zipfile.return_value = mock_zip

        assert not os.path.isdir(sub_path)

        unzip("", sub_path)

        extract_args = mock_zip.extract_arguments

        assert os.path.isdir(sub_path)
        assert extract_args[0] == sub_path
