import pathlib

from matl_online.public.models import Release
from matl_online.settings import Config

from .source import github_repository, remove_source_directory


def refresh_releases(
    repository: str = Config.MATL_REPOSITORY,
    source_root: pathlib.Path = Config.MATL_SOURCE_DIRECTORY,
) -> None:
    """Fetch new release information from GitHub and update local database."""
    repo = github_repository(repository)

    for release in repo.get_releases():
        # Skip any pre-releases
        if release.prerelease:
            continue

        version = release.tag_name

        # Check if we already have this release in the database
        release_record = Release.query.filter_by(tag=version).first()

        # If there is no existing record, create it
        if release_record is None:
            Release.create(tag=version, date=release.published_at)
            continue

        # Check if our local release is stale
        if release.published_at > release_record.date:
            # Clear our cache of the source code
            remove_source_directory(version, source_root=source_root)

            # Now update the database entry
            release_record.update(date=release.published_at)
