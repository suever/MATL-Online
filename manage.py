#!/usr/bin/env python

"""Management script."""
import os

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Server, Shell
from flask_script.commands import Clean, ShowUrls

from settings import DevConfig, ProdConfig

CONFIG = ProdConfig if os.environ.get('MATL_ONLINE_ENV') == 'prod' else DevConfig
HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

from app import app, db

manager = Manager(app)
migrate = Migrate(app, db)


def _make_context():
    """Return context dict for a shell session so you can access app, db, and the User model by default."""
    return {'app': app, 'db': db}


manager.add_command('server', Server())
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('urls', ShowUrls())
manager.add_command('clean', Clean())

if __name__ == '__main__':
    manager.run()
