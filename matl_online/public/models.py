"""SQLAlchemy models."""
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from flask import current_app
from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property

from matl_online.database import Column, Model, db


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
        """Get the latest release from Github."""
        releases = cls.query.all()
        if len(releases) == 0:
            return None

        releases.sort(key=lambda x: x.version)
        return releases[-1]


class DocumentationLink(Model):
    """Model for storing hyperlinks to MATLAB's documentation."""

    __tablenamme__ = 'doclinks'

    id = Column(db.Integer, primary_key=True)
    name = Column(db.String, unique=True, nullable=False)
    link = Column(db.String, nullable=False)

    @classmethod
    def refresh(cls):
        """Fetch updated documentation from the Mathworks."""
        # Flip the order of the links so that the first URL listed is the
        # highest priority and will take precedence
        for url in current_app.config['MATLAB_DOC_LINKS'][::-1]:
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')

            terms = soup.findAll('td', {'class': 'term'})
            links = [term.find('a') for term in terms]

            for link in links:

                function = link.text.rstrip()

                doc = cls.query.filter_by(name=function).first()
                doc_url = urljoin(url, link['href'])

                # Create an entry if one doesn't already exist
                if doc is None:
                    doc = cls(name=function)

                doc.link = doc_url
                doc.save()

        # Make sure to remove i and j entries
        toremove = cls.query.filter(or_(cls.name == 'i', cls.name == 'j')).all()
        for item in toremove:
            item.delete()

        return cls.query.all()
