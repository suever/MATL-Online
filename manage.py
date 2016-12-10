#!/usr/bin/env python
"""Management script."""

import eventlet
import os

from glob import glob
from subprocess import call

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Server, Shell, Command, Option
from flask_script.commands import Clean, ShowUrls

from matl_online.app import create_app, socketio
from matl_online.database import db
from matl_online import matl
from matl_online.settings import config
from matl_online.analytics.utils import fetch_answers

eventlet.monkey_patch()

app = create_app(config)

manager = Manager(app)
migrate = Migrate(app, db)


def _make_context():
    """Return context dict for a shell session."""
    return {'app': app, 'db': db}


@manager.command
def test():
    """Run the tests."""
    import pytest
    test_path = os.path.join(config.PROJECT_ROOT, 'tests')
    exit_code = pytest.main([test_path, '--verbose'])
    return exit_code


@manager.command
def refresh_releases():
    """Update MATL release information."""
    matl.refresh_releases()


@manager.command
def refresh_answers():
    """Update the local database of submitted answers."""
    fetch_answers()


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
            if rv != 0:
                exit(rv)

        if fix_imports:
            execute_tool('Fixing import order', 'isort', '-rc')
        execute_tool('Checking code style', 'flake8')


@manager.command
def run(port=5000, host='127.0.0.1'):
    """Command for creating an eventlet instance."""
    socketio.run(app, host=host, port=int(port), use_reloader=True)


manager.add_command('server', Server())
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('urls', ShowUrls())
manager.add_command('clean', Clean())
manager.add_command('lint', Lint())

if __name__ == '__main__':
    manager.run()
