# SmartInsight Global - 快速命令参考

## 测试命令

### 运行所有测试
```bash
./run_tests.sh
```

### 后端测试

#### 运行所有后端测试（需要数据库）
```bash
cd backend && pytest -p no:napari -v tests
```

#### 运行核心测试（不需要数据库）
```bash
cd backend && pytest -p no:napari -v -k "not (test_news or test_llm_endpoints)" tests
```

#### 运行特定测试文件
```bash
cd backend && pytest -p no:napari -v tests/test_core/test_analyzer.py
```

#### 生成覆盖率报告（需要修复 SQLite 问题）
```bash
cd backend && pytest -p no:napari --cov=app --cov-report=html tests
open backend/htmlcov/index.html
```

### 前端测试

#### 运行所有前端测试
```bash
cd frontend && npm test
```

#### 运行特定测试文件
```bash
cd frontend && npm test -- Dashboard.test.tsx
```

#### 生成覆盖率报告
```bash
cd frontend && npm run test:coverage
```

## 开发命令

### 启动后端服务
```bash
cd backend && ./step1.start_backend.sh
```

### 启动 Celery Worker
```bash
cd backend && ./step2.start_celery.sh
```

### 启动前端服务
```bash
cd frontend && npm run dev
```

## 数据库命令

### 启动测试数据库（Docker）
```bash
docker run -d --name test-postgres \
  -e POSTGRES_USER=test \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=test_smartinsight \
  -p 5433:5432 \
  postgres:15-alpine
```

### 检查数据库连接
```bash
psql -h localhost -p 5433 -U test -d test_smartinsight
```

### 停止测试数据库
```bash
docker stop test-postgres && docker rm test-postgres
```

## 代码质量

### Python代码格式化
```bash
cd backend && black app tests
```

### Python代码检查
```bash
cd backend && flake8 app tests
```

### TypeScript代码检查
```bash
cd frontend && npm run lint
```

## Git工作流

### 创建feature分支
```bash
git checkout -b feature/v1.2-testing
```

### 提交更改
```bash
git add .
git commit -m "feat: add V1.2 testing infrastructure"
```

### 推送到远程
```bash
git push origin feature/v1.2-testing
```

## 调试技巧

### 运行单个测试并显示详细输出
```bash
cd backend && pytest -p no:napari -vv -s tests/test_core/test_analyzer.py::TestNewsAnalyzer::test_sentiment_analysis_positive
```

### 在测试失败时进入调试器
```bash
cd backend && pytest -p no:napari --pdb tests
```

### 显示测试执行时间
```bash
cd backend && pytest -p no:napari --durations=10 tests
```

## 性能分析

### 后端性能分析
```bash
cd backend && python -m cProfile -o profile.stats test_analysis.py
python -m pstats profile.stats
```

### 前端性能分析
```bash
cd frontend && npm run build
# 查看 .next/build-manifest.json
```

## 故障排除

### 清理Python缓存
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 清理前端缓存
```bash
cd frontend && rm -rf .next node_modules
npm install
```

### 重置测试数据库
```bash
docker stop test-postgres && docker rm test-postgres
# 然后重新启动
```

## 快捷别名（添加到 ~/.zshrc）

```bash
# SmartInsight Global aliases
alias sig-test='cd /path/to/SmartInsightGlobal && ./run_tests.sh'
alias sig-backend='cd /path/to/SmartInsightGlobal/backend && ./step1.start_backend.sh'
alias sig-frontend='cd /path/to/SmartInsightGlobal/frontend && npm run dev'
alias sig-worker='cd /path/to/SmartInsightGlobal/backend && ./step2.start_celery.sh'
```
