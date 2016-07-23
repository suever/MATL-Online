#!/usr/bin/env python

"""Worker module for creating celery workers."""

from matl_online.app import create_app, celery
from matl_online.settings import DevConfig

app = create_app(DevConfig)
app.app_context().push()
celery.conf.update(app.config)
