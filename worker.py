#!/usr/bin/env python
from matl_online.app import celery, create_app
from matl_online.settings import DevConfig
from matl_online.tasks import *

app = create_app(DevConfig)
app.app_context().push()
