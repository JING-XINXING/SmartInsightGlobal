#!/bin/bash

# Start Celery beat scheduler for periodic tasks
celery -A app.worker.celery_app beat --loglevel=info
