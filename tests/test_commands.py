from flask import Flask
from pytest_mock.plugin import MockerFixture


def test_refresh_releases_command(mocker: MockerFixture, app: Flask) -> None:
    # Mock out the actual refresh_releases function
    refresh_releases = mocker.patch("matl_online.commands.releases.refresh_releases")

    # Use the CLI to invoke the command
    runner = app.test_cli_runner()
    runner.invoke(args=["refresh_releases"])

    # And ensure it had the intended behavior
    refresh_releases.assert_called_once()
