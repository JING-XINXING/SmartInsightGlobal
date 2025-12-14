#!/bin/bash
#
# SmartInsight Global - 数据库恢复脚本
#
# 功能：
#   - 从备份文件恢复 PostgreSQL 数据库
#   - 支持 .sql 和 .sql.gz 格式
#   - 可选择恢复到新数据库
#
# 使用方法：
#   ./restore.sh <备份文件路径> [目标数据库名]
#
# 示例：
#   ./restore.sh ~/backups/smartinsight/smartinsight_20250129.sql.gz
#   ./restore.sh ~/backups/smartinsight/smartinsight_20250129.sql.gz smartinsight_test
#

set -e

# ==================== 配置区域 ====================

DB_HOST="${POSTGRES_SERVER:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"
DEFAULT_DB="${POSTGRES_DB:-smartinsight}"

# ==================== 函数定义 ====================

# 日志函数
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}"
}

# 显示帮助
show_help() {
    cat << EOF
SmartInsight Global - 数据库恢复脚本

用法：
    ./restore.sh <备份文件路径> [目标数据库名]

参数：
    备份文件路径    要恢复的备份文件（支持 .sql 或 .sql.gz）
    目标数据库名    可选，默认为 $DEFAULT_DB

环境变量：
    POSTGRES_SERVER     数据库服务器地址（默认: localhost）
    POSTGRES_PORT       数据库端口（默认: 5432）
    POSTGRES_USER       数据库用户名（默认: postgres）
    POSTGRES_PASSWORD   数据库密码
    POSTGRES_DB         默认数据库名（默认: smartinsight）

示例：
    ./restore.sh ~/backups/smartinsight/smartinsight_20250129.sql.gz
    ./restore.sh backup.sql.gz smartinsight_test

警告：
    恢复操作会覆盖目标数据库中的现有数据！
    建议在恢复前先备份当前数据。
EOF
}

# 检查备份文件
check_backup_file() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        log "ERROR" "备份文件不存在: $file"
        exit 1
    fi
    
    if [[ ! "$file" =~ \.(sql|sql\.gz)$ ]]; then
        log "ERROR" "不支持的文件格式，请使用 .sql 或 .sql.gz 文件"
        exit 1
    fi
    
    log "INFO" "备份文件: $file"
    log "INFO" "文件大小: $(ls -lh "$file" | awk '{print $5}')"
}

# 确认恢复
confirm_restore() {
    local target_db="$1"
    
    echo ""
    echo "================================================"
    echo "  警告：即将恢复数据库"
    echo "  目标数据库: $target_db"
    echo "  服务器: $DB_HOST:$DB_PORT"
    echo "  此操作将覆盖现有数据！"
    echo "================================================"
    echo ""
    
    read -p "确认继续？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "INFO" "用户取消恢复操作"
        exit 0
    fi
}

# 执行恢复
perform_restore() {
    local backup_file="$1"
    local target_db="$2"
    
    log "INFO" "开始恢复数据库..."
    log "INFO" "目标数据库: $target_db"
    
    # 检查数据库是否存在，不存在则创建
    PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d postgres \
        -tc "SELECT 1 FROM pg_database WHERE datname = '$target_db'" | grep -q 1 || {
            log "INFO" "数据库 $target_db 不存在，正在创建..."
            PGPASSWORD="${POSTGRES_PASSWORD:-}" createdb \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                "$target_db"
            log "INFO" "数据库 $target_db 创建成功"
        }
    
    # 根据文件类型恢复
    if [[ "$backup_file" =~ \.gz$ ]]; then
        log "INFO" "解压并恢复..."
        gunzip -c "$backup_file" | PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$target_db" \
            --quiet \
            2>&1 | while read line; do
                [[ "$line" =~ ^(ERROR|FATAL) ]] && log "ERROR" "$line" || true
            done
    else
        log "INFO" "恢复 SQL 文件..."
        PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$target_db" \
            -f "$backup_file" \
            --quiet \
            2>&1 | while read line; do
                [[ "$line" =~ ^(ERROR|FATAL) ]] && log "ERROR" "$line" || true
            done
    fi
    
    log "INFO" "恢复完成!"
}

# 验证恢复结果
verify_restore() {
    local target_db="$1"
    
    log "INFO" "验证恢复结果..."
    
    # 检查表数量
    local table_count=$(PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$target_db" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    
    # 检查新闻数量
    local news_count=$(PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$target_db" \
        -t -c "SELECT COUNT(*) FROM news" 2>/dev/null || echo "0")
    
    log "INFO" "数据库表数量: $(echo $table_count | tr -d ' ')"
    log "INFO" "新闻记录数量: $(echo $news_count | tr -d ' ')"
}

# ==================== 主流程 ====================

main() {
    # 检查参数
    if [ $# -lt 1 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
        show_help
        exit 0
    fi
    
    local backup_file="$1"
    local target_db="${2:-$DEFAULT_DB}"
    
    log "INFO" "========================================="
    log "INFO" "SmartInsight Global - 数据库恢复"
    log "INFO" "========================================="
    
    # 1. 检查备份文件
    check_backup_file "$backup_file"
    
    # 2. 确认恢复
    confirm_restore "$target_db"
    
    # 3. 执行恢复
    perform_restore "$backup_file" "$target_db"
    
    # 4. 验证结果
    verify_restore "$target_db"
    
    log "INFO" "恢复完成!"
}

main "$@"
