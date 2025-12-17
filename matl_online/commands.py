"""Custom Flask CLI Commands."""

from flask import Flask

from matl_online.matl import releases


def register_commands(app: Flask) -> None:
    """Register custom commands with the flask CLI."""

    @app.cli.command(name="refresh_releases", help="Update MATL releases from GitHub")  # type: ignore[untyped-decorator]
    def refresh_releases() -> None:
        """Command for updating all release information."""
        releases.refresh_releases()
