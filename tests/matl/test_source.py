import pathlib
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from pytest_mock.plugin import MockerFixture

from matl_online.errors import MissingDirectory
from matl_online.matl.source import (
    get_matl_folder,
    github_repository,
    install_matl,
    remove_source_directory,
)


class TestRemoveSourceDirectory:
    def test_no_directory(self, tmp_path: pathlib.Path) -> None:
        # Given a MATL version that does not exist
        version = "0.0.0"

        assert not tmp_path.joinpath(version).is_dir()

        # When removing the source directory
        remove_source_directory(version, tmp_path)

        # Then the directories are as expected
        assert tmp_path.is_dir()
        assert not tmp_path.joinpath(version).is_dir()

    def test_directory_exists(self, tmp_path: pathlib.Path) -> None:
        # Given a MATL version that does exist
        version = "1.2.3"

        # A source directory that exists
        source_directory = tmp_path.joinpath(version)
        source_directory.mkdir()

        assert source_directory.is_dir()

        # And a file in that directory
        source_directory.joinpath("testfile.txt").touch()

        # When removing the source directory
        remove_source_directory(version, tmp_path)

        # The directory is removed
        assert not source_directory.is_dir()
        assert tmp_path.is_dir()


def test_github_repository(mocker: MockerFixture) -> None:
    # Given a repository
    repository = "suever/matl-online"

    github_mock = mocker.patch("matl_online.matl.source.github")

    # When retrieving the PyGithub repository object for this repository
    repo = github_repository(repository)

    # It queries the expected repository
    github_mock.get_repo.assert_called_once_with(repository)


class TestInstallMATL:
    def test_successful_response(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        # Given a MATL version to install
        version = "0.0.0"

        # And a repository to install it from
        repository = "suever/matl-online"

        download_link = "https://example.com"

        repository_mock = MagicMock()
        mocker.patch(
            "matl_online.matl.source.github_repository",
            return_value=repository_mock,
        )

        repository_mock.get_archive_link.return_value = download_link

        response_mock = MagicMock()
        get_mock = mocker.patch(
            "matl_online.matl.source.requests.get", return_value=response_mock
        )
        response_mock.content = b"123"
        response_mock.status_code = 200

        unzip_mock = mocker.patch("matl_online.matl.source.unzip")
        mocker.patch("matl_online.matl.source.BytesIO", return_value=b"123io")

        # When installing MATL
        install_matl(version, folder=tmp_path, repository=repository)

        # It has the intended side effects
        repository_mock.get_archive_link.assert_called_once_with("zipball", version)
        get_mock.assert_called_once_with(download_link, stream=True)
        unzip_mock.assert_called_once_with(b"123io", tmp_path)

    def test_failure_response(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        # Given a MATL version to install
        version = "0.0.0"

        # And a repository to install it from
        repository = "suever/matl-online"

        download_link = "https://example.com"

        repository_mock = MagicMock()
        mocker.patch(
            "matl_online.matl.source.github_repository",
            return_value=repository_mock,
        )

        repository_mock.get_archive_link.return_value = download_link

        response_mock = MagicMock()
        get_mock = mocker.patch(
            "matl_online.matl.source.requests.get", return_value=response_mock
        )

        response_mock.content = b"123"
        response_mock.status_code = 404

        # When installing MATL, the expected exception is raised
        with pytest.raises(KeyError):
            install_matl(version, folder=tmp_path, repository=repository)

        # It has the intended side effects
        repository_mock.get_archive_link.assert_called_once_with("zipball", version)
        get_mock.assert_called_once_with(download_link, stream=True)


class TestGetMATLFolder:
    """Series of tests to check if source code is managed properly."""

    def test_no_source_no_install(self, tmp_path: pathlib.Path) -> None:
        # Given a specific version that we do not currently have the source for
        version = "18.3.0"

        # When trying to get the directory containing the source and asking
        # to not install MATL, the expected exception is raised
        with pytest.raises(MissingDirectory):
            get_matl_folder(version, install=False, source_root=tmp_path)

    def test_missing_source_install(
        self,
        tmp_path: pathlib.Path,
        mocker: MockerFixture,
    ) -> None:
        # Given a particular version that does not yet exist
        version = "0.0.0"

        mock_install = mocker.patch("matl_online.matl.source.install_matl")

        # When trying to get the source location of the version
        result = get_matl_folder(version, install=True, source_root=tmp_path)

        # Then the version was installed
        mock_install.assert_called_once_with(version, tmp_path.joinpath(version))

        # And the result returned the expected path
        assert result == tmp_path.joinpath("0.0.0")

    def test_source_already_exists(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        # Given a particular version of MATL
        version = "1.2.3"

        mock_install = mocker.patch("matl_online.matl.source.install_matl")

        # And a folder that already exists in this location
        source_folder = tmp_path.joinpath(version)
        source_folder.mkdir()

        assert source_folder.is_dir()

        # When trying to get the source location of the version
        result = get_matl_folder(version, install=True, source_root=tmp_path)

        # Then the existing installation is used
        mock_install.assert_not_called()
        assert result == source_folder
