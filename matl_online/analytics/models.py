"""SQLAlchemy Models."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import backref

from matl_online.database import db, Model, Column, relationship


class StackExchangeUser(Model):
    """Model for storing users who answer questions using MATL."""

    __tablename__ = 'se_users'

    id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, nullable=False, index=True)

    username = Column(db.String)
    profile_url = Column(db.String)
    avatar_url = Column(db.String)

    __cache__ = {}

    @classmethod
    def from_cache(cls, user_id, fallback=None):
        if user_id in cls.__cache__:
            print('Hit cache')
            return cls.__cache__[user_id]

        # Fallback to a lookup in the database
        user = cls.query.filter(cls.user_id == user_id).first()

        if user:
            print('Lookup in database')
            cls.__cache__[user_id] = user
            return user


class Answer(Model):
    """Model for storing previous answers."""

    __tablename__ = 'answers'

    id = Column(db.Integer, primary_key=True)

    answer_id = Column(db.Integer, unique=True)

    # Information about who provided the answer
    owner_id = db.Column(db.Integer, ForeignKey('se_users.user_id'))
    owner = relationship('StackExchangeUser', backref=backref('answers'))

    # Title of the answered question
    title = Column(db.String)

    question_id = Column(db.Integer)

    accepted = Column(db.Boolean)

    created = Column(db.DateTime)
    updated = Column(db.DateTime)

    score = Column(db.Integer)

    url = Column(db.String)

    # The MATL source code found within the post
    source_code = Column(db.String)
