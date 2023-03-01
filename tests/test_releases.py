"""Unit tests for checking database models and behavior."""

from datetime import datetime

import pytest
from flask_sqlalchemy import SQLAlchemy

from matl_online.public.models import Release

from .factories import ReleaseFactory


@pytest.mark.usefixtures("db")
class TestRelease:
    """Series of tests for the Release database model."""

    def test_get_latest(self) -> None:
        """Make sure that the expected release is returned as the latest."""

        # Create 3 release each time checking that the latest is the latest
        # release
        for k in range(3):
            # Ensure that this is the latest release
            new_release = ReleaseFactory.create()
            latest_release = Release.latest()
            assert latest_release
            assert new_release == latest_release

        # Now add a new entry that has an old date
        release = Release.create(date=datetime(2000, 1, 1), tag="1.2.3")

        # Make sure that this is NOT the latest release
        assert release != Release.latest()

        # Now add a release that is old but has a higher release number
        release = Release.create(date=datetime(1999, 1, 1), tag="100.0.0")

        assert release == Release.latest()

    def test_empty_releases_latest(self) -> None:
        """Make sure that if we don't have any releases, we don't have issues."""
        assert Release.query.count() == 0
        assert Release.latest() is None
        assert Release.query.all() == []

    def test_release_ordering(self) -> None:
        """Make sure that we sort the releases properly."""
        release1: Release = ReleaseFactory.build(tag="9.0.0")
        release2 = ReleaseFactory.build(tag="9.0.1")
        release3 = ReleaseFactory.build(tag="9.1.0")
        release4 = ReleaseFactory.build(tag="10.0.0")

        assert release2.version > release1.version
        assert release3.version > release1.version
        assert release3.version > release2.version
        assert release4.version > release3.version

    def test_release_ordering_truncated(self) -> None:
        """Make sure that even if we don't have 3 parts, we sort correctly."""
        release1: Release = ReleaseFactory.build(tag="9")
        release2 = ReleaseFactory.build(tag="9.0.1")
        release3 = ReleaseFactory.build(tag="9.1")
        release4 = ReleaseFactory.build(tag="9.1.2")
        release5 = ReleaseFactory.build(tag="10")

        assert release2.version > release1.version
        assert release3.version > release2.version
        assert release4.version > release3.version
        assert release5.version > release4.version

    def test_remove_release(self) -> None:
        """Make sure that we can delete a release if needed."""
        num = 10
        ReleaseFactory.create_batch(size=num)  # type: ignore[attr-defined]

        releases = Release.query.all()

        assert len(releases) == num

        # Remove the last release
        last_release = releases[-1]
        last_release.delete()

        releases = Release.query.all()

        assert len(releases) == num - 1
        assert Release.query.filter_by(tag=last_release.tag).all() == []

    def test_release_update(self) -> None:
        """Any details of a release can be updated programmatically."""
        old_date = datetime(2000, 1, 1)
        old_tag = "1.2.3"
        release = Release.create(date=old_date, tag=old_tag)

        assert release.date == old_date

        # Make sure that we can update the time
        new_date = datetime(2001, 1, 1)

        release.update(date=new_date)

        assert release.date == new_date

        # Make sure we can update the tag
        new_tag = "4.5.6"

        assert release.tag == old_tag

        release.update(tag=new_tag)

        assert release.tag == new_tag

    def test_release_repr(self) -> None:
        """Check that the release is displayed properly if coerced."""
        release: Release = ReleaseFactory.build(tag="1.2.3")
        assert release.__repr__() == "<Release %r>" % "1.2.3"

    def test_factory(self, db: SQLAlchemy) -> None:
        """Ensure that the factory is working as expected."""
        now = datetime.now()
        release: Release = ReleaseFactory.build(date=now)
        db.session.commit()

        assert bool(release.tag)
        assert isinstance(release, Release)
        assert release.date == now
