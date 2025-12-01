#!/bin/bash
#
# SmartInsight Global - 本地数据库备份脚本
# 
# 功能：
#   - 使用 pg_dump 导出 PostgreSQL 数据库
#   - 使用 gzip 压缩备份文件
#   - 按日期命名备份文件
#   - 自动清理过期备份（默认保留30天）
#
# 使用方法：
#   ./backup_local.sh [备份目录] [保留天数]
#
# 示例：
#   ./backup_local.sh                          # 使用默认设置
#   ./backup_local.sh ~/backups/smartinsight 14 # 自定义目录，保留14天
#

set -e  # 遇到错误立即退出

# ==================== 配置区域 ====================

# 默认配置（可通过环境变量覆盖）
DB_HOST="${POSTGRES_SERVER:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-smartinsight}"
DB_USER="${POSTGRES_USER:-xinxingjing}"

# 备份目录（可通过参数覆盖）
BACKUP_DIR="${1:-${BACKUP_DIR:-$HOME/backups/smartinsight}}"

# 保留天数（可通过参数覆盖）
RETENTION_DAYS="${2:-${RETENTION_DAYS:-30}}"

# 日期格式
DATE_FORMAT=$(date +%Y%m%d_%H%M%S)
DATE_SHORT=$(date +%Y%m%d)

# 备份文件名
BACKUP_FILE="smartinsight_${DATE_FORMAT}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

# 日志配置
LOG_FILE="${BACKUP_DIR}/backup.log"

# ==================== 函数定义 ====================

# 日志函数
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

# 创建备份目录
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "INFO" "创建备份目录: $BACKUP_DIR"
    fi
}

# 执行数据库备份
perform_backup() {
    log "INFO" "开始备份数据库: $DB_NAME"
    log "INFO" "数据库服务器: $DB_HOST:$DB_PORT"
    log "INFO" "备份文件: $BACKUP_DIR/$BACKUP_FILE_GZ"
    
    # 使用 pg_dump 导出并压缩
    PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-acl \
        --verbose \
        2>> "$LOG_FILE" | gzip > "$BACKUP_DIR/$BACKUP_FILE_GZ"
    
    # 检查备份文件
    if [ -f "$BACKUP_DIR/$BACKUP_FILE_GZ" ]; then
        local file_size=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE_GZ" | awk '{print $5}')
        log "INFO" "备份成功! 文件大小: $file_size"
        return 0
    else
        log "ERROR" "备份失败: 备份文件未生成"
        return 1
    fi
}

# 清理过期备份
cleanup_old_backups() {
    log "INFO" "清理 $RETENTION_DAYS 天前的备份文件..."
    
    local count=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        log "INFO" "删除过期备份: $(basename "$file")"
        ((count++)) || true
    done < <(find "$BACKUP_DIR" -name "smartinsight_*.sql.gz" -type f -mtime +$RETENTION_DAYS -print0)
    
    if [ $count -gt 0 ]; then
        log "INFO" "共删除 $count 个过期备份"
    else
        log "INFO" "没有需要清理的过期备份"
    fi
}

# 列出最近的备份
list_recent_backups() {
    log "INFO" "最近的备份文件:"
    ls -lht "$BACKUP_DIR"/smartinsight_*.sql.gz 2>/dev/null | head -10 | while read line; do
        log "INFO" "  $line"
    done
}

# 获取备份统计
get_backup_stats() {
    local total_count=$(ls -1 "$BACKUP_DIR"/smartinsight_*.sql.gz 2>/dev/null | wc -l)
    local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    log "INFO" "备份统计: 共 $total_count 个文件, 总大小 $total_size"
}

# 发送通知（可选，需要配置）
send_notification() {
    local status="$1"
    local message="$2"
    
    # 如果配置了 webhook URL，发送通知
    if [ -n "$BACKUP_WEBHOOK_URL" ]; then
        curl -s -X POST "$BACKUP_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"status\": \"$status\", \"message\": \"$message\", \"timestamp\": \"$(date -Iseconds)\"}" \
            > /dev/null 2>&1 || true
    fi
}

# ==================== 主流程 ====================

main() {
    log "INFO" "========================================="
    log "INFO" "SmartInsight Global - 数据库备份"
    log "INFO" "========================================="
    
    # 1. 创建备份目录
    create_backup_dir
    
    # 2. 执行备份
    if perform_backup; then
        # 3. 清理过期备份
            cleanup_old_backups
        
        # 4. 显示统计
        list_recent_backups
        get_backup_stats
        
        log "INFO" "备份完成!"
        send_notification "success" "数据库备份成功: $BACKUP_FILE_GZ"
        exit 0
    else
        log "ERROR" "备份失败!"
        send_notification "error" "数据库备份失败"
            exit 1
    fi
}

# 运行主程序
main "$@"
