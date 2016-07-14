from datetime import datetime

from factory import Sequence, LazyFunction
from factory.alchemy import SQLAlchemyModelFactory

from matl_online.database import db
from matl_online.public.models import Release


class BaseFactory(SQLAlchemyModelFactory):

    class Meta:
        abstract = True
        sqlalchemy_session = db.session


class ReleaseFactory(BaseFactory):

    tag = Sequence(lambda n: '{0}.0.0'.format(n))
    date = LazyFunction(datetime.now)

    class Meta:
        model = Release
