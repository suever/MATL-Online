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
            release = ReleaseFactory(date=datetime.now())

            # Ensure that this is the latest release
            assert release == Release.latest()

        # Now add a new entry that has an old date
        release = ReleaseFactory(date=datetime(2000,1,1))

        # Make sure that this is NOT the latest release
        assert release != Release.latest()

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
