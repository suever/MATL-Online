"""SQLAlchemy models."""
import operator
from typing import List, Optional, Tuple

from sqlalchemy.ext.hybrid import hybrid_property

from matl_online.database import Column, Model, db


class Release(Model):
    """Model for storing metadata associated with MATL releases."""

    __tablename__ = "releases"

    id = Column(db.Integer, primary_key=True)
    tag = Column(db.String, unique=True, nullable=False)
    date = Column(db.DateTime, unique=True, nullable=False)

    def __repr__(self) -> str:
        """Create a custom string representation."""
        return "<Release %r>" % self.tag

    @hybrid_property
    def version(self) -> Tuple[int, ...]:
        """Convert release number to tuple for comparisons."""
        return tuple(int(x) for x in self.tag.split("."))

    @classmethod
    def latest(cls) -> Optional["Release"]:
        """Get the latest release from GitHub."""
        releases: List[Release] = cls.query.all()
        if len(releases) == 0:
            return None

        releases = sorted(releases, key=operator.attrgetter("version"))
        return releases[-1]

    @classmethod
    def exists(cls, tag: str) -> bool:
        """Checks if the specified release exists."""
        match = cls.query.filter_by(tag=tag).one_or_none()
        return match is not None
