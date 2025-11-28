# SmartInsight Global (智察全球)

> 智能全球情报分析系统 - 实时采集、分析和解读全球资讯

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-16-black.svg)

## 📖 项目简介

SmartInsight Global 是一个智能化的全球资讯采集与分析平台，通过整合多个国际主流媒体的 RSS 源，实时获取全球新闻动态，并计划集成国产大模型进行深度分析。

### 核心特性

- 🌍 **全球视野**: 聚合 BBC、The Guardian、NYT、Al Jazeera 等主流媒体
- 🤖 **智能分析**: 计划集成 DeepSeek/Qwen 等国产 LLM 进行情感分析和趋势预测
- 💾 **数据安全**: PostgreSQL 数据库 + 双重备份机制（本地 + 云端）
- 📊 **可视化**: 现代化 Web 界面，实时展示全球资讯动态
- ⚡ **高性能**: 异步架构，Celery 定时任务，Redis 缓存

## 🏗️ 技术架构

### 后端
- **框架**: FastAPI (Python 3.12)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **任务队列**: Celery
- **ORM**: SQLAlchemy (Async)
- **迁移**: Alembic

### 前端
- **框架**: Next.js 16 (App Router)
- **UI**: React 19 + TailwindCSS v4
- **组件库**: Shadcn/UI
- **图标**: Lucide React
- **语言**: TypeScript

## 🚀 快速开始

### 前置要求

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd SmartInsightGlobal
```

#### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

#### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 4. 启动 Celery Worker (可选)

```bash
cd backend

# 启动 Worker
./start_worker.sh

# 启动定时调度器
./start_beat.sh
```

### 访问应用

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📁 项目结构

```
SmartInsightGlobal/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置和工具
│   │   │   ├── config.py   # 配置管理
│   │   │   ├── crawler.py  # RSS 采集器
│   │   │   └── celery_app.py
│   │   ├── crud/           # 数据库操作
│   │   ├── db/             # 数据库配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── worker.py       # Celery 任务
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt
├── frontend/               # 前端应用
│   ├── app/
│   │   ├── page.tsx        # 主页面
│   │   └── layout.tsx
│   ├── components/         # React 组件
│   ├── lib/                # 工具函数
│   └── package.json
├── docs/                   # 文档
│   ├── 智察全球_项目开发计划.md
│   └── 开发进度报告.md
└── docker-compose.yml      # Docker 配置
```

## 🔧 配置说明

### 环境变量

在 `backend/.env` 中配置：

```env
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=smartinsight
POSTGRES_PORT=5432

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM API Keys (未来使用)
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## 📊 数据采集

### 当前支持的新闻源

- BBC News World
- The Guardian World News
- New York Times World
- Al Jazeera

### 手动触发采集

```bash
cd backend
python test_worker.py
```

### 自动采集

Celery Beat 会每小时自动执行采集任务。

## 🛣️ 开发路线图

### ✅ MVP 阶段 (已完成 85%)
- [x] 基础架构搭建
- [x] RSS 采集引擎
- [x] 数据库设计与迁移
- [x] RESTful API
- [x] 前端新闻列表页面
- [x] Celery 定时任务
- [ ] 错误处理与日志

### 🚧 V1.0 阶段 (进行中)
- [ ] AI 智能分析引擎
- [ ] 情感分析
- [ ] 关键词提取
- [ ] 全球热点地图
- [ ] 风险指数看板
- [ ] 数据备份系统

### 📅 V1.1 阶段 (计划中)
- [ ] 移动端适配 (PWA)
- [ ] 全文检索
- [ ] 日报/周报生成
- [ ] 多语言支持

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，请提交 Issue。

---

**最后更新**: 2025-11-28
