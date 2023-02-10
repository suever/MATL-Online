import pathlib
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pytest_mock.plugin import MockerFixture

from matl_online.matl.releases import refresh_releases
from matl_online.public.models import Release

TEST_DATA_DIRECTORY = pathlib.Path(__file__).parents[1].joinpath("data").absolute()


def _mock_release(
    version: str,
    prerelease: bool = False,
    published_at: Optional[datetime] = None,
) -> MagicMock:
    mock = MagicMock()
    mock.prerelease = prerelease
    mock.tag_name = version
    mock.published_at = published_at or datetime.now()

    return mock


class TestReleaseRefresh:
    """Tests for updating our local release database from GitHub."""

    def test_all_new(self, mocker: MockerFixture, app: Flask, db: SQLAlchemy) -> None:
        """Completely populate the database (no previous entries)."""
        repository_mock = MagicMock()
        mocker.patch(
            "matl_online.matl.releases.github_repository",
            return_value=repository_mock,
        )

        releases = [
            _mock_release("1.2.3"),
            _mock_release("4.5.6"),
            _mock_release("7.8.9"),
        ]

        repository_mock.get_releases.return_value = releases

        # When refreshing the releases
        refresh_releases()

        # Then when querying the database for all releases
        release_records = Release.query.all()

        # The expected releases exist
        assert len(release_records) == len(releases)

        for k, release in enumerate(release_records):
            assert release.tag == releases[k].tag_name

    def test_prerelease(
        self,
        mocker: MockerFixture,
        app: Flask,
        db: SQLAlchemy,
    ) -> None:
        """Ensure that pre-releases are ignored."""
        repository_mock = MagicMock()
        mocker.patch(
            "matl_online.matl.releases.github_repository",
            return_value=repository_mock,
        )

        releases = [
            _mock_release("1.2.3"),
            _mock_release("4.5.6", prerelease=True),
            _mock_release("7.8.9"),
        ]

        repository_mock.get_releases.return_value = releases

        # When refreshing the releases
        refresh_releases()

        # Then when querying the database for all releases
        release_records = Release.query.all()

        # The expected releases exist
        assert len(release_records) == len(releases) - 1

        tags = [x.tag for x in release_records]

        assert tags == ["1.2.3", "7.8.9"]

    def test_updated_release(
        self,
        mocker: MockerFixture,
        app: Flask,
        db: SQLAlchemy,
        tmp_path: pathlib.Path,
    ) -> None:
        """Updated releases should be updated in our database."""
        repository_mock = MagicMock()
        mocker.patch(
            "matl_online.matl.releases.github_repository",
            return_value=repository_mock,
        )

        remove_directory_mock = mocker.patch(
            "matl_online.matl.releases.remove_source_directory"
        )

        # Given an old version of a release
        Release.create(date=datetime(2000, 1, 1), tag="1.2.3")

        # And three releases from the API
        releases = [
            _mock_release("1.2.3"),
            _mock_release("4.5.6"),
            _mock_release("7.8.9"),
        ]

        repository_mock.get_releases.return_value = releases

        # When refreshing the releases
        refresh_releases(source_root=tmp_path)

        # Assert the invalid source code was removed
        remove_directory_mock.assert_called_once_with("1.2.3", source_root=tmp_path)

        # Ensure the old release was updated
        original_release = Release.query.filter_by(tag="1.2.3").one()

        assert original_release.date == releases[0].published_at
