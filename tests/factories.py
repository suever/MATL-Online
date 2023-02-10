"""Some factories for quickly generating model instances."""

from datetime import datetime

from factory import LazyFunction, Sequence
from factory.alchemy import SQLAlchemyModelFactory

from matl_online.database import db
from matl_online.public.models import Release


class BaseFactory(SQLAlchemyModelFactory):  # type: ignore
    """Base factory for SQLAlchemy Model generation."""

    class Meta:
        """Meta information for the factory."""

        abstract = True
        sqlalchemy_session = db.session


class ReleaseFactory(BaseFactory):
    """Factory for creating Release objects on demand."""

    tag = Sequence(lambda n: "{0}.0.0".format(n))
    date = LazyFunction(datetime.now)

    class Meta:
        """Meta information for the factory."""

        model = Release
