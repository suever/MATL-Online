"""Custom Flask CLI Commands."""

from flask import Flask

from matl_online import matl


def register_commands(app: Flask) -> None:
    """Register custom commands with the flask CLI."""

    @app.cli.command(name="refresh_releases", help="Update MATL releases from GitHub")  # type: ignore[misc]
    def refresh_releases() -> None:
        """Command for updating all release information."""
        matl.refresh_releases()
