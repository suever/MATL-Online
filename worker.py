#!/usr/bin/env python

"""Worker module for creating celery workers."""

from matl_online.app import celery, create_app
from typing import Any
from matl_online.settings import config

from pathlib import Path

from celery.signals import heartbeat_sent, worker_ready, worker_shutdown

app = create_app(config)
app.app_context().push()
celery.conf.update(app.config)


HEARTBEAT_FILE = Path(config.CELERY_WORKER_HEARTBEAT_FILE)
READINESS_FILE = Path(config.CELERY_WORKER_READINESS_FILE)


@heartbeat_sent.connect
def heartbeat(**_: Any) -> None:
    HEARTBEAT_FILE.touch()


@worker_ready.connect
def worker_ready_callback(**_: Any) -> None:
    READINESS_FILE.touch()


@worker_shutdown.connect
def worker_shutdown_callback(**_: Any) -> None:
    for f in (HEARTBEAT_FILE, READINESS_FILE):
        f.unlink()
