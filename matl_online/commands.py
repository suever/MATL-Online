"""Custom Flask CLI Commands."""

import os

from matl_online import matl
from matl_online.settings import config


def register_commands(app):
    """Register custom commands with the flask CLI."""
    @app.cli.command(
        name='test',
        help='Run unit tests'
    )
    def test():
        import pytest
        test_path = os.path.join(config.PROJECT_ROOT, 'tests')
        return pytest.main([test_path, '--verbose'])

    @app.cli.command(
        name='refresh_releases',
        help='Update MATL releases from GitHub'
    )
    def refresh_releases():
        """Command for updating all release information."""
        matl.refresh_releases()
