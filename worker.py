#!/usr/bin/env python

from matl_online.app import create_app, celery # NOQA
from matl_online.settings import DevConfig

app = create_app(DevConfig)
app.app_context().push()
