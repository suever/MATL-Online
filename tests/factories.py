"""Some factories for quickly generating model instances."""

from datetime import datetime

from factory import LazyAttribute, LazyFunction, Sequence
from factory.alchemy import SQLAlchemyModelFactory

from matl_online.database import db
from matl_online.public.models import DocumentationLink, Release


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory for SQLAlchemy Model generation."""

    class Meta:
        """Meta information for the factory."""

        abstract = True
        sqlalchemy_session = db.session


class ReleaseFactory(BaseFactory):
    """Factory for creating Release objects on demand."""

    tag = Sequence(lambda n: '{0}.0.0'.format(n))
    date = LazyFunction(datetime.now)

    class Meta:
        """Meta information for the factory."""

        model = Release


class DocumentationLinkFactory(BaseFactory):
    """Factory for creating DocumentationLink objects on demand."""

    # The default link will simply append .html to the end of the name
    link = LazyAttribute(lambda o: o.name + '.html')

    class Meta:
        """Meta information for the factory."""

        model = DocumentationLink
