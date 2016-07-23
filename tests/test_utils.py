""""Unit tests for utils module."""

import os
import shutil

from matl_online.utils import unzip
from .mocks import MockZipFile


class TestUnzip:
    """Test unzip functionality."""

    def test_unzip_and_flatten(self, mocker, tmpdir):
        """Check that flattening of parent directories works as expected."""
        mzip = MockZipFile()
        mzip.add_files('mydir/abcde', 'mydir/fghij')

        zipfile = mocker.patch('matl_online.utils.zipfile.ZipFile')
        zipfile.return_value = mzip

        unzip('', tmpdir.strpath)

        extract_args = mzip.extract_arguments

        assert len(extract_args) == 2
        assert extract_args[0] == tmpdir.strpath

        outnames = [obj.filename for obj in extract_args[1]]

        assert len(outnames) == 2
        assert outnames[0] == 'abcde'
        assert outnames[1] == 'fghij'

    def test_unzip_without_flatten(self, mocker, tmpdir):
        """Check that unzipping (without flattening) works."""
        mzip = MockZipFile()
        mzip.add_files('mydir/abcde', 'mydir/fghij')

        zipfile = mocker.patch('matl_online.utils.zipfile.ZipFile')
        zipfile.return_value = mzip

        unzip('', tmpdir.strpath, flatten=False)

        extract_args = mzip.extract_arguments

        assert len(extract_args) == 1
        assert extract_args[0] == tmpdir.strpath

    def test_non_existent_dir(self, mocker, tmpdir):
        """If destination doesn't exist, make sure it's created."""
        subdir = tmpdir.mkdir('sub')
        subpath = subdir.strpath
        shutil.rmtree(subpath)

        mzip = MockZipFile()
        mzip.add_files('mydic/abcde', 'mydir/fghij')

        zipfile = mocker.patch('matl_online.utils.zipfile.ZipFile')
        zipfile.return_value = mzip

        assert not os.path.isdir(subpath)

        unzip('', subpath)

        extract_args = mzip.extract_arguments

        assert os.path.isdir(subpath)
        assert extract_args[0] == subpath
