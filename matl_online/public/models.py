from sqlalchemy import desc

from matl_online.database import db, Model, Column


class Release(Model):

    __tablename__ = 'releases'

    id = Column(db.Integer, primary_key=True)
    tag = Column(db.String, unique=True, nullable=False)
    date = Column(db.DateTime, unique=True, nullable=False)

    def __repr__(self):
        return '<Release %r>' % self.tag

    @classmethod
    def latest(cls):
        return cls.query.order_by(desc(cls.date)).first()
