#!/bin/bash

# SmartInsight Global 测试运行脚本
# 支持单元测试、集成测试、覆盖率报告等

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认值
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/frontend"
TEST_TYPE=""
COVERAGE=false
VERBOSE=false
PARALLEL=false
INTEGRATION=false

# 显示帮助信息
show_help() {
    echo -e "${BLUE}SmartInsight Global 测试运行脚本${NC}"
    echo ""
    echo "用法: $0 [选项] [测试类型]"
    echo ""
    echo "测试类型:"
    echo "  unit              运行单元测试"
    echo "  integration       运行集成测试"
    echo "  api              运行API测试"
    echo "  models           运行模型测试"
    echo "  all              运行所有测试"
    echo "  coverage         运行测试并生成覆盖率报告"
    echo ""
    echo "选项:"
    echo "  -v, --verbose    详细输出"
    echo "  -c, --coverage    生成覆盖率报告"
    echo "  -p, --parallel     并行运行测试"
    echo "  -i, --integration 仅运行集成测试"
    echo "  -h, --help       显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 unit -c                    运行单元测试并生成覆盖率"
    echo "  $0 all --coverage             运行所有测试并生成覆盖率"
    echo "  $0 integration -v             详细运行集成测试"
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -c|--coverage)
                COVERAGE=true
                shift
                ;;
            -p|--parallel)
                PARALLEL=true
                shift
                ;;
            -i|--integration)
                INTEGRATION=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            unit|integration|api|models|all|coverage)
                if [[ -n "$TEST_TYPE" ]]; then
                    echo -e "${RED}错误: 只能指定一个测试类型${NC}"
                    exit 1
                fi
                TEST_TYPE=$1
                shift
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi

    # 检查Node.js (用于前端测试)
    if [[ "$TEST_TYPE" == "all" ]] && ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi

    # 检查Docker (用于集成测试)
    if [[ "$INTEGRATION" == "true" ]] && ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi

    log_info "依赖检查完成"
}

# 设置测试环境
setup_test_env() {
    log_info "设置测试环境..."

    # 设置Python路径
    export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

    # 设置测试环境变量
    export TEST_MODE="true"
    export DATABASE_URL="postgresql+asyncpg://test:test@localhost:5433/test_smartinsight"
    export REDIS_URL="redis://localhost:6380/1"

    log_verbose "Python路径: $PYTHONPATH"
    log_verbose "测试数据库: $DATABASE_URL"
    log_verbose "测试Redis: $REDIS_URL"
}

# 启动测试服务
start_test_services() {
    if [[ "$INTEGRATION" == "true" ]]; then
        log_info "启动测试服务..."

        # 检查Docker是否运行
        if ! docker info > /dev/null 2>&1; then
            log_error "Docker未运行，无法启动测试服务"
            exit 1
        fi

        # 启动测试数据库和Redis
        cd "$BACKEND_DIR"
        docker-compose -f docker-compose.test.yml up -d

        # 等待服务启动
        log_info "等待服务启动..."
        sleep 5

        # 检查服务健康状态
        if ! docker-compose -f docker-compose.test.yml ps | grep -q "Up"; then
            log_error "测试服务启动失败"
            exit 1
        fi

        log_info "测试服务已启动"
    fi
}

# 停止测试服务
stop_test_services() {
    if [[ "$INTEGRATION" == "true" ]]; then
        log_info "停止测试服务..."
        cd "$BACKEND_DIR"
        docker-compose -f docker-compose.test.yml down
        log_info "测试服务已停止"
    fi
}

# 运行后端测试
run_backend_tests() {
    log_info "运行后端测试..."

    cd "$BACKEND_DIR"

    # 激活虚拟环境（如果存在）
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
    fi

    # 安装测试依赖
    log_info "安装测试依赖..."
    pip install -r requirements-test.txt

    # 构建测试命令
    local pytest_cmd="pytest tests/"
    local pytest_args=""

    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args="$pytest_args -v"
    fi

    if [[ "$COVERAGE" == "true" ]]; then
        pytest_args="$pytest_args --cov=app --cov-report=xml:./test-results/coverage.xml --cov-report=html:./test-results/html --cov-report=term-missing"
    fi

    if [[ "$PARALLEL" == "true" ]]; then
        pytest_args="$pytest_args -n auto"
    fi

    # 添加测试类型过滤
    case "$TEST_TYPE" in
        unit)
            pytest_args="$pytest_args -m unit"
            ;;
        integration)
            pytest_args="$pytest_args -m integration"
            ;;
        api)
            pytest_args="$pytest_args -m api"
            ;;
        models)
            pytest_args="$pytest_args -m unit -k test_models"
            ;;
        all)
            pytest_args="$pytest_args"
            ;;
    esac

    # 执行测试
    local test_exit_code=0
    eval "$pytest_cmd $pytest_args" || test_exit_code=$?

    return $test_exit_code
}

# 运行前端测试
run_frontend_tests() {
    log_info "运行前端测试..."

    cd "$FRONTEND_DIR"

    # 安装依赖
    log_info "安装前端依赖..."
    npm ci

    # 构建测试命令
    local npm_cmd="npm run test"
    local npm_args=""

    if [[ "$VERBOSE" == "true" ]]; then
        npm_args="-- --verbose"
    fi

    if [[ "$COVERAGE" == "true" ]]; then
        npm_cmd="npm run test:coverage"
    fi

    # 执行测试
    eval "$npm_cmd $npm_args" || return $?
}

# 生成覆盖率报告
generate_coverage_report() {
    log_info "生成测试覆盖率报告..."

    if [[ "$TEST_TYPE" == "backend" || "$TEST_TYPE" == "all" ]]; then
        log_info "后端测试覆盖率报告已生成: $BACKEND_DIR/test-results/"

        if [[ "$COVERAGE" == "true" ]]; then
            log_info "HTML覆盖率报告: $BACKEND_DIR/test-results/html/index.html"
            log_info "XML覆盖率报告: $BACKEND_DIR/test-results/coverage.xml"
        fi
    fi

    if [[ "$TEST_TYPE" == "frontend" || "$TEST_TYPE" == "all" ]]; then
        log_info "前端测试覆盖率报告已生成: $FRONTEND_DIR/coverage/"

        if [[ "$COVERAGE" == "true" ]]; then
            log_info "HTML覆盖率报告: $FRONTEND_DIR/coverage/lcov-report/index.html"
        fi
    fi
}

# 清理测试环境
cleanup_test_env() {
    log_info "清理测试环境..."

    # 停止测试服务
    stop_test_services

    # 清理临时文件
    rm -rf "$BACKEND_DIR/test-results"
    rm -rf "$FRONTEND_DIR/coverage"

    log_info "清理完成"
}

# 显示测试结果摘要
show_test_summary() {
    local backend_exit_code=$1
    local frontend_exit_code=$2

    echo ""
    echo -e "${BLUE}=== 测试结果摘要 ===${NC}"
    echo ""

    if [[ -n "$backend_exit_code" ]]; then
        if [[ $backend_exit_code -eq 0 ]]; then
            echo -e "${GREEN}✓ 后端测试: 通过${NC}"
        else
            echo -e "${RED}✗ 后端测试: 失败 (退出码: $backend_exit_code)${NC}"
        fi
    fi

    if [[ -n "$frontend_exit_code" ]]; then
        if [[ $frontend_exit_code -eq 0 ]]; then
            echo -e "${GREEN}✓ 前端测试: 通过${NC}"
        else
            echo -e "${RED}✗ 前端测试: 失败 (退出码: $frontend_exit_code)${NC}"
        fi
    fi

    if [[ "$COVERAGE" == "true" ]]; then
        echo ""
        echo -e "${BLUE}📊 覆盖率报告:${NC}"
        if [[ "$TEST_TYPE" == "backend" || "$TEST_TYPE" == "all" ]]; then
            echo "  后端: $BACKEND_DIR/test-results/html/index.html"
        fi
        if [[ "$TEST_TYPE" == "frontend" || "$TEST_TYPE" == "all" ]]; then
            echo "  前端: $FRONTEND_DIR/coverage/lcov-report/index.html"
        fi
    fi

    echo ""
}

# 主函数
main() {
    # 解析参数
    if [[ $# -eq 0 ]]; then
        log_error "必须指定测试类型"
        show_help
        exit 1
    fi

    parse_args "$@"

    # 默认启用覆盖率
    if [[ "$TEST_TYPE" == "coverage" ]]; then
        COVERAGE=true
        TEST_TYPE="all"
    fi

    log_info "开始运行 SmartInsight Global 测试..."
    log_verbose "测试类型: $TEST_TYPE"
    log_verbose "详细输出: $VERBOSE"
    log_verbose "生成覆盖率: $COVERAGE"
    log_verbose "并行运行: $PARALLEL"
    log_verbose "集成测试: $INTEGRATION"

    # 检查依赖
    check_dependencies

    # 设置测试环境
    setup_test_env

    # 启动测试服务（集成测试）
    start_test_services

    # 运行测试
    local backend_exit_code=0
    local frontend_exit_code=0

    # 根据测试类型运行相应测试
    case "$TEST_TYPE" in
        unit|api|models|integration)
            run_backend_tests
            backend_exit_code=$?
            ;;
        coverage)
            COVERAGE=true
            TEST_TYPE="all"
            run_backend_tests
            backend_exit_code=$?
            run_frontend_tests
            frontend_exit_code=$?
            ;;
        all)
            run_backend_tests
            backend_exit_code=$?
            run_frontend_tests
            frontend_exit_code=$?
            ;;
    esac

    # 生成覆盖率报告
    if [[ "$COVERAGE" == "true" ]]; then
        generate_coverage_report
    fi

    # 停止测试服务
    stop_test_services

    # 显示测试结果摘要
    show_test_summary $backend_exit_code $frontend_exit_code

    # 返回合适的退出码
    if [[ $backend_exit_code -ne 0 || $frontend_exit_code -ne 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# 错误处理
trap 'log_error "测试过程中发生错误，正在清理..."; cleanup_test_env; exit 1' ERR INT TERM

# 执行主函数
main "$@"