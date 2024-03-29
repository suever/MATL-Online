"""Unit tests for testing the development and production configurations."""

import os

from matl_online import app
from matl_online.settings import (
    DevConfig,
    ProdConfig,
    _get_cors_allowed_origins,
    get_config,
)
from prometheus_flask_exporter import PrometheusMetrics  # type: ignore[import]


def test_production_config(metrics: PrometheusMetrics) -> None:
    """Production config."""
    app.metrics = metrics
    flask_app = app.create_app(ProdConfig)
    assert flask_app.config["ENV"] == "prod"
    assert flask_app.config["DEBUG"] is False
    assert flask_app.config["ASSETS_DEBUG"] is False


def test_dev_config(metrics: PrometheusMetrics) -> None:
    """Development config."""
    app.metrics = metrics
    flask_app = app.create_app(DevConfig)
    assert flask_app.config["ENV"] == "dev"
    assert flask_app.config["DEBUG"] is True
    assert flask_app.config["ASSETS_DEBUG"] is True


def test_prod_config_lookup() -> None:
    """Ensure that we load the proper config."""
    os.environ["MATL_ONLINE_ENV"] = "prod"

    assert get_config() == ProdConfig


def test_dev_config_lookup() -> None:
    """Ensure that we load the proper config."""
    os.environ["MATL_ONLINE_ENV"] = "dev"

    assert get_config() == DevConfig


class TestGetCORSAllowedOrigins:
    def test_not_provided(self) -> None:
        # Unset the environment variable
        os.unsetenv("CORS_ALLOWED_ORIGINS")

        assert _get_cors_allowed_origins() == []

    def test_empty_string(self) -> None:
        # Set the CORS allowed origins to an empty string
        os.environ["CORS_ALLOWED_ORIGINS"] = ""

        assert _get_cors_allowed_origins() == []

    def test_single_value(self) -> None:
        # Set the CORS allowed origin to a single origin
        os.environ["CORS_ALLOWED_ORIGINS"] = "matl.io"

        assert _get_cors_allowed_origins() == ["matl.io"]

    def test_multiple_values(self) -> None:
        # Set the CORS allowed origin to multiple origins
        os.environ["CORS_ALLOWED_ORIGINS"] = "matl.io;localhost:5000"

        assert _get_cors_allowed_origins() == ["matl.io", "localhost:5000"]
