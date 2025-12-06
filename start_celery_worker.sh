#!/bin/bash
# SmartInsightGlobal Celery 启动脚本

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:/Users/xinxingjing/AI/SmartInsightGlobal/backend"
cd /Users/xinxingjing/AI/SmartInsightGlobal/backend

echo "正在启动 Celery Worker..."

# 启动 Celery Worker
# -A app.worker.celery_app: 指定 Celery App
# --loglevel=info: 设置日志级别
# --concurrency=4: 设置并发进程数
# --without-gossip: 禁用 gossip 协议
# --without-mingle: 禁用 mingle
# --without-heartbeat: 禁用心跳
celery -A app.worker.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat &

WORKER_PID=$!
echo "Celery Worker 已启动，PID: $WORKER_PID"

# 等待几秒钟确保 Worker 启动成功
sleep 3

# 检查 Worker 是否正在运行
if ps -p $WORKER_PID > /dev/null; then
    echo "✅ Celery Worker 启动成功"

    # 测试 Worker 连接
    echo "正在测试 Worker 连接..."
    celery -A app.worker.celery_app inspect ping

    # 显示活动任务
    echo "当前活动任务:"
    celery -A app.worker.celery_app inspect active
else
    echo "❌ Celery Worker 启动失败"
    exit 1
fi

echo "Worker 进程信息:"
ps aux | grep celery | grep -v grep