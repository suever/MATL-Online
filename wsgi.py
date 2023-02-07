"""Script for initializing a production app for use with uwsgi."""

import eventlet

eventlet.monkey_patch()

from matl_online.app import create_app  # noqa: E402
from matl_online.settings import get_config  # noqa: E402

app = create_app(get_config())
