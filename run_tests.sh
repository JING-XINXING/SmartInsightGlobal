#!/bin/bash
# SmartInsight Global - 测试运行脚本
# 自动运行后端和前端测试

set -e

echo "🧪 SmartInsight Global V1.2 - 测试套件"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 后端测试
echo "📦 运行后端测试..."
echo "-------------------"

cd backend

# 检查PostgreSQL是否在5433端口运行
if lsof -Pi :5433 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL test database is running on port 5433${NC}"
    echo "Running ALL backend tests (including database tests)..."
    pytest -p no:napari -v tests
else
    echo -e "${YELLOW}⚠️  PostgreSQL test database NOT running on port 5433${NC}"
    echo "Running backend tests (excluding database tests)..."
    pytest -p no:napari -v -k "not (test_news or test_llm_endpoints)" tests
fi

BACKEND_EXIT_CODE=$?

cd ..

# 前端测试
echo ""
echo "🎨 运行前端测试..."
echo "-------------------"

cd frontend
npm test -- --watchAll=false --passWithNoTests

FRONTEND_EXIT_CODE=$?

cd ..

# 总结
echo ""
echo "📊 测试结果总结"
echo "==============="

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 后端测试通过${NC}"
else
    echo -e "${RED}❌ 后端测试失败 (退出码: $BACKEND_EXIT_CODE)${NC}"
fi

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 前端测试通过${NC}"
else
    echo -e "${RED}❌ 前端测试失败 (退出码: $FRONTEND_EXIT_CODE)${NC}"
fi

# 返回整体状态
if [ $BACKEND_EXIT_CODE -eq 0 ] && [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ 部分测试失败${NC}"
    exit 1
fi
