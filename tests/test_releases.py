import pytest

from datetime import datetime

from matl_online.public.models import Release
from .factories import ReleaseFactory


@pytest.mark.usefixtures('db')
class TestRelease:

    def test_get_latest(self):
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
        # Make sure that we can delete a release if needed
        nRelease = 10
        ReleaseFactory.create_batch(size=nRelease)

        releases = Release.query.all()

        assert len(releases) == nRelease

        # Remove the last release
        last_release = releases[-1]
        last_release.delete()

        releases = Release.query.all()

        assert len(releases) == nRelease - 1
        assert Release.query.filter_by(tag=last_release.tag).all() == []

    def test_release_repr(self):
        # Check that the release is displayed properly if coerced
        release = ReleaseFactory(tag='1.2.3')
        assert release.__repr__() == '<Release %r>' % '1.2.3'

    def test_factory(self, db):
        """
        Ensure that the factory is working as expected
        """

        now = datetime.now()
        release = ReleaseFactory(date=now)
        db.session.commit()

        assert bool(release.tag)
        assert isinstance(release, Release)
        assert release.date == now
