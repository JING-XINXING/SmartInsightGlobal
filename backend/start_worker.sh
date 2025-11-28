#!/bin/bash

# Start Celery worker
celery -A app.worker.celery_app worker --loglevel=info
