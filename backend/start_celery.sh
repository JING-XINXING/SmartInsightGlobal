#!/bin/bash

# 启动 Celery Worker 和 Beat
# Worker: 执行任务
# Beat: 调度定时任务

echo "Starting Celery Worker and Beat..."

# 启动 worker（后台运行）
celery -A app.worker.celery_app worker --loglevel=info &
WORKER_PID=$!

# 等待一秒确保 worker 启动
sleep 1

# 启动 beat（前台运行）
celery -A app.worker.celery_app beat --loglevel=info

# 如果 beat 退出，也杀掉 worker
kill $WORKER_PID
