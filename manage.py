#!/usr/bin/env python

import eventlet
eventlet.monkey_patch()

"""Management script."""
import requests
import os

from glob import glob
from subprocess import call

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Server, Shell, Command, Option
from flask_script.commands import Clean, ShowUrls

from matl_online.app import create_app, socketio
from matl_online.database import db
from matl_online.settings import DevConfig, ProdConfig
from matl_online.utils import parse_iso8601
from matl_online.public.models import Release

if os.environ.get('MATL_ONLINE_ENV') == 'prod':
    CONFIG = ProdConfig
else:
    CONFIG = DevConfig

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

app = create_app(CONFIG)

manager = Manager(app)
migrate = Migrate(app, db)


def _make_context():
    """
    Return context dict for a shell session so you can access app, db,
    and the User model by default.
    """
    return {'app': app, 'db': db}


@manager.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main([TEST_PATH, '--verbose'])
    return exit_code


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


class Lint(Command):
    """Lint and check code style with flake8 and isort."""

    def get_options(self):
        """Command line options."""
        return (
            Option('-f', '--fix-imports',
                   action='store_true', dest='fix_imports', default=False,
                   help='Fix imports using isort, before linting'),
        )

    def run(self, fix_imports):
        """Run command."""
        skip = ['requirements', 'env', 'migrations']
        root_files = glob('*.py')

        root_directories = list()

        for name in next(os.walk('.'))[1]:
            if not name.startswith('.'):
                root_directories.append(name)

        files_and_directories = list()

        for arg in root_files + root_directories:
            if arg not in skip:
                files_and_directories.append(arg)

        def execute_tool(description, *args):
            """Execute a checking tool with its arguments."""
            command_line = list(args) + files_and_directories
            print('{}: {}'.format(description, ' '.join(command_line)))
            rv = call(command_line)
            if rv is not 0:
                exit(rv)

        if fix_imports:
            execute_tool('Fixing import order', 'isort', '-rc')
        execute_tool('Checking code style', 'flake8')


@manager.command
def run():
    socketio.run(app,
                 host='127.0.0.1',
                 port=5000,
                 use_reloader=True)


manager.add_command('server', Server())
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('urls', ShowUrls())
manager.add_command('clean', Clean())
manager.add_command('lint', Lint())

if __name__ == '__main__':
    manager.run()
