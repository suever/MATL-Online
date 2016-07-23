"""Unit tests for checking database models and behavior."""

import pytest

from datetime import datetime

from matl_online.public.models import Release
from .factories import ReleaseFactory


@pytest.mark.usefixtures('db')
class TestRelease:
    """Series of tests for the Release database model."""

    def test_get_latest(self):
        """Make sure that the expected release is returned as the latest."""
        # Create 3 release each time checking that the latest is the latest
        # release
        for k in range(3):
            # Ensure that this is the latest release
            assert ReleaseFactory() == Release.latest()

        # Now add a new entry that has an old date
        release = Release.create(date=datetime(2000, 1, 1), tag='1.2.3')

        # Make sure that this is NOT the latest release
        assert release != Release.latest()

    def test_remove_release(self):
        """Make sure that we can delete a release if needed."""
        num = 10
        ReleaseFactory.create_batch(size=num)

        releases = Release.query.all()

        assert len(releases) == num

        # Remove the last release
        last_release = releases[-1]
        last_release.delete()

        releases = Release.query.all()

        assert len(releases) == num - 1
        assert Release.query.filter_by(tag=last_release.tag).all() == []

    def test_release_update(self):
        """Any details of a release can be updated programmatically."""
        olddate = datetime(2000, 1, 1)
        oldtag = '1.2.3'
        release = Release.create(date=olddate, tag=oldtag)

        assert release.date == olddate

        # Make sure that we can update the time
        newdate = datetime(2001, 1, 1)

        release.update(date=newdate)

        assert release.date == newdate

        # Make sure we can update the tag
        newtag = '4.5.6'

        assert release.tag == oldtag

        release.update(tag=newtag)

        assert release.tag == newtag

    def test_release_repr(self):
        """Check that the release is displayed properly if coerced."""
        release = ReleaseFactory(tag='1.2.3')
        assert release.__repr__() == '<Release %r>' % '1.2.3'

    def test_factory(self, db):
        """Ensure that the factory is working as expected."""
        now = datetime.now()
        release = ReleaseFactory(date=now)
        db.session.commit()

        assert bool(release.tag)
        assert isinstance(release, Release)
        assert release.date == now
