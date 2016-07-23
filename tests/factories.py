"""Some factories for quickly generating model instances."""

from datetime import datetime

from factory import Sequence, LazyFunction
from factory.alchemy import SQLAlchemyModelFactory

from matl_online.database import db
from matl_online.public.models import Release


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory for SQLAlchemy Model generation."""

    class Meta:
        abstract = True
        sqlalchemy_session = db.session


class ReleaseFactory(BaseFactory):
    """Factory for creating Release objects on demand."""

    tag = Sequence(lambda n: '{0}.0.0'.format(n))
    date = LazyFunction(datetime.now)

    class Meta:
        model = Release
