"""Some factories for quickly generating model instances."""

from datetime import datetime
from typing import TypeVar

from factory import LazyAttribute, LazyFunction, Sequence
from factory.alchemy import SQLAlchemyModelFactory
from factory.builder import Resolver

from matl_online.database import db
from matl_online.public.models import DocumentationLink, Release

T = TypeVar("T")


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


def link_generator(link: "Resolver[None]") -> str:
    return str(link.name) + ".html"


class DocumentationLinkFactory(BaseFactory):
    """Factory for creating DocumentationLink objects on demand."""

    # The default link will simply append .html to the end of the name
    link = LazyAttribute(link_generator)

    class Meta:
        """Meta information for the factory."""

        model = DocumentationLink
