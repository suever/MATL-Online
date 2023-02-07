"""Custom Flask CLI Commands."""

from matl_online import matl


def register_commands(app):
    """Register custom commands with the flask CLI."""

    @app.cli.command(name="refresh_releases", help="Update MATL releases from GitHub")
    def refresh_releases():
        """Command for updating all release information."""
        matl.refresh_releases()
