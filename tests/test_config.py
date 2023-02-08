"""Unit tests for testing the development and production configurations."""

import os

from matl_online.app import create_app
from matl_online.settings import DevConfig, ProdConfig, get_config


def test_production_config() -> None:
    """Production config."""
    app = create_app(ProdConfig)
    assert app.config["ENV"] == "prod"
    assert app.config["DEBUG"] is False
    assert app.config["ASSETS_DEBUG"] is False


def test_dev_config() -> None:
    """Development config."""
    app = create_app(DevConfig)
    assert app.config["ENV"] == "dev"
    assert app.config["DEBUG"] is True
    assert app.config["ASSETS_DEBUG"] is True


def test_prod_config_lookup() -> None:
    """Ensure that we load the proper config."""
    os.environ["MATL_ONLINE_ENV"] = "prod"

    assert get_config() == ProdConfig


def test_dev_config_lookup() -> None:
    """Ensure that we load the proper config."""
    os.environ["MATL_ONLINE_ENV"] = "dev"

    assert get_config() == DevConfig
