"""SQLAlchemy models."""

from sqlalchemy.ext.hybrid import hybrid_property

from matl_online.database import db, Model, Column


class Release(Model):
    """Model for storing metadata associated with MATL releases."""

    __tablename__ = 'releases'

    id = Column(db.Integer, primary_key=True)
    tag = Column(db.String, unique=True, nullable=False)
    date = Column(db.DateTime, unique=True, nullable=False)

    def __repr__(self):
        """Create a custom string representation."""
        return '<Release %r>' % self.tag

    @hybrid_property
    def version(self):
        """Convert release number to tuple for comparisons."""
        return tuple(int(x) for x in self.tag.split('.'))

    @classmethod
    def latest(cls):
        """Method for getting the latest release."""
        releases = cls.query.all()
        if len(releases) == 0:
            return None

        releases.sort(key=lambda x: x.version)
        return releases[-1]
