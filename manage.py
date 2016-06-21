#!/usr/bin/env python

"""Management script."""
import requests
import os

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Server, Shell
from flask_script.commands import Clean, ShowUrls

from matl_online.app import create_app
from matl_online.database import db
from matl_online.settings import DevConfig, ProdConfig
from matl_online.utils import parse_iso8601
from matl_online.public.models import Release

CONFIG = ProdConfig if os.environ.get('MATL_ONLINE_ENV') == 'prod' else DevConfig
HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

app = create_app(CONFIG)

manager = Manager(app)
migrate = Migrate(app, db)


def _make_context():
    """Return context dict for a shell session so you can access app, db, and the User model by default."""
    return {'app': app, 'db': db}


@manager.command
def refresh_releases():
    """
    Fetch new release information from Github and update local database
    """
    url = 'https://api.github.com/repos/%s/releases' % app.config['MATL_REPO']
    resp = requests.get(url)

    for item in resp.json():
        if item['prerelease']:
            continue

        release = Release.query.filter(Release.tag == item['tag_name']).first()

        if release is None:
            Release.create(tag=item['tag_name'],
                           date=parse_iso8601(item['published_at']))


manager.add_command('server', Server())
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('urls', ShowUrls())
manager.add_command('clean', Clean())

if __name__ == '__main__':
    manager.run()
