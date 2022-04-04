"""Script for initializing a production app for use with uwsgi."""

import eventlet

eventlet.monkey_patch()

from matl_online.app import create_app
from matl_online.settings import get_config

app = create_app(get_config())
