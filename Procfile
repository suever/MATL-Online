web: $VIRTUAL_ENV/bin/gunicorn --worker-class eventlet -b 127.0.0.1:$PORT -w 1 wsgi:app
worker: $VIRTUAL_ENV/bin/celery worker -A worker.celery --autoscale=4,2 --purge -Ofair -l INFO