#!/bin/bash
cd /Users/xinxingjing/AI/SmartInsightGlobal/backend
celery -A app.worker.celery_app worker --loglevel=info
