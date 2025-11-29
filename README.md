# SmartInsight Global (智察全球)

> 智能全球情报分析系统 - 实时采集、分析和解读全球资讯

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-16-black.svg)
![Status](https://img.shields.io/badge/status-V1.0%20Released-green.svg)

## 📖 项目简介

SmartInsight Global 是一个智能化的全球资讯采集与分析平台，通过整合多个国际主流媒体的 RSS 源，实时获取全球新闻动态，并集成国产大模型进行深度分析。

### 核心特性

- 🌍 **全球视野**: 聚合 BBC、The Guardian、NYT、Al Jazeera、Reuters 等 17+ 主流媒体
- 🤖 **智能分析**: 已集成 DeepSeek/Qwen/Moonshot/智谱/百川/MiniMax 等 6 大国产 LLM
- 📊 **情感分析**: 自动分析新闻情感倾向 (-100 到 100)
- 🏷️ **关键词提取**: AI 自动提取 3-5 个关键词
- 📑 **智能分类**: 12 个预定义类别自动分类
- 📈 **数据可视化**: 仪表盘展示情感分布、分类统计、热门关键词
- ⏰ **定时任务**: 可配置的自动采集和分析频率
- 📄 **分页浏览**: 支持分页查看新闻列表
- ⚡ **高性能**: 异步架构，Celery 定时任务，Redis 缓存

## 🏗️ 技术架构

### 后端
- **框架**: FastAPI (Python 3.9+)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **任务队列**: Celery + Celery Beat
- **ORM**: SQLAlchemy (Async)
- **迁移**: Alembic
- **AI**: 统一 LLM Client (OpenAI 兼容格式)

### 前端
- **框架**: Next.js 16 (App Router)
- **UI**: React 19 + TailwindCSS v4
- **组件库**: Shadcn/UI
- **图表**: Recharts
- **图标**: Lucide React
- **语言**: TypeScript

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd SmartInsightGlobal
```

#### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

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

# LLM API Keys (至少配置一个)
DEEPSEEK_API_KEY=sk-your-deepseek-key
QWEN_API_KEY=sk-your-qwen-key
MOONSHOT_API_KEY=sk-your-moonshot-key
ZHIPU_API_KEY=your-zhipu-key
BAICHUAN_API_KEY=sk-your-baichuan-key
MINIMAX_API_KEY=your-minimax-key
```

#### 3. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

#### 4. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 5. 启动 Celery Worker (定时任务)

```bash
cd backend

# 启动 Worker
celery -A app.worker.celery_app worker --loglevel=info

# 启动定时调度器 (另一个终端)
celery -A app.worker.celery_app beat --loglevel=info
```

### 访问应用

- **前端界面**: http://localhost:3000
- **数据分析仪表盘**: http://localhost:3000/dashboard
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📁 项目结构

```
SmartInsightGlobal/
├── backend/                     # 后端服务
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   └── api_v1/
│   │   │       └── endpoints/
│   │   │           ├── news.py      # 新闻 API (分页、详情)
│   │   │           ├── llm.py       # LLM 配置 API
│   │   │           └── scheduler.py # 定时任务配置 API
│   │   ├── core/               # 核心模块
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── crawler.py      # RSS 采集器
│   │   │   ├── analyzer.py     # AI 分析引擎
│   │   │   ├── llm_client.py   # 统一 LLM 客户端
│   │   │   ├── scheduler_config.py # 调度器配置
│   │   │   ├── celery_app.py   # Celery 配置
│   │   │   └── logger.py       # 日志系统
│   │   ├── crud/               # 数据库操作
│   │   ├── db/                 # 数据库配置
│   │   ├── models/             # 数据模型
│   │   ├── schemas/            # Pydantic 模式
│   │   ├── worker.py           # Celery 任务
│   │   └── main.py             # 应用入口
│   ├── alembic/                # 数据库迁移
│   ├── logs/                   # 日志文件
│   └── requirements.txt
├── frontend/                   # 前端应用
│   ├── app/
│   │   ├── page.tsx            # 首页 (分页新闻列表)
│   │   ├── dashboard/
│   │   │   └── page.tsx        # 数据分析仪表盘
│   │   └── layout.tsx
│   ├── components/
│   │   ├── Dashboard.tsx       # 仪表盘组件
│   │   ├── LLMSelector.tsx     # LLM 模型选择器
│   │   ├── SchedulerSettings.tsx # 定时任务设置
│   │   └── ui/                 # Shadcn/UI 组件
│   ├── lib/
│   │   ├── types.ts            # TypeScript 类型
│   │   └── utils.ts            # 工具函数
│   └── package.json
├── docs/                       # 文档
├── scripts/                    # 脚本
├── docker-compose.yml          # Docker 配置
└── .env                        # 环境变量
```

## 📊 功能说明

### 首页 - 新闻列表
- 分页浏览新闻 (每页 20/30/50 篇可选)
- 显示新闻标题、来源、时间、分类、情感分数
- 显示 AI 提取的关键词标签
- 按来源统计侧边栏

### 数据分析仪表盘
- **AI 模型选择**: 选择 LLM 厂商和具体模型
- **定时任务设置**: 配置采集和分析频率
- **核心指标卡片**: 总文章数、平均情感、风险指数、分析完成度
- **可视化图表**:
  - 情感分布饼图
  - 新闻分类柱状图
  - 来源分布图
  - 热门关键词列表

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/news/` | GET | 获取新闻列表 |
| `/api/v1/news/paginated` | GET | 分页获取新闻 |
| `/api/v1/news/{id}` | GET | 获取新闻详情 |
| `/api/v1/llm/providers` | GET | 获取 LLM 厂商列表 |
| `/api/v1/llm/models/{provider}` | GET | 获取厂商模型列表 |
| `/api/v1/llm/update-config` | POST | 更新 LLM 配置 |
| `/api/v1/scheduler/config` | GET/POST | 获取/更新定时任务配置 |

## 📰 支持的新闻源

- BBC News World
- The Guardian World News
- New York Times World
- Al Jazeera
- Reuters World
- AP News World
- CNN World
- CNBC World
- Washington Post World
- Deutsche Welle
- France 24
- NHK World
- South China Morning Post
- Times of India
- TechCrunch
- The Economist

## 🛣️ 开发路线图

### ✅ MVP 阶段 (100% 完成)
- [x] 基础架构搭建
- [x] RSS 采集引擎
- [x] 数据库设计与迁移
- [x] RESTful API
- [x] 前端新闻列表页面
- [x] Celery 定时任务
- [x] 日志系统

### ✅ V1.0 阶段 (100% 完成)
- [x] AI 智能分析引擎
- [x] 情感分析
- [x] 关键词提取
- [x] 新闻分类
- [x] 数据可视化仪表盘
- [x] LLM 模型选择器
- [x] 定时任务 Web 配置
- [x] 新闻列表分页

### 🚧 V1.1 阶段 (计划中)
- [ ] 数据备份系统
- [ ] 新闻详情页 (前端)
- [ ] 全文检索
- [ ] 全球热点地图
- [ ] 事件时间轴
- [ ] PWA 移动端支持
- [ ] AI 日报/周报生成

## 🔧 常见问题

### Q: 为什么 LLM 厂商显示"未配置"？
A: 确保在 `.env` 文件中配置了对应厂商的 API Key，然后重启后端服务。

### Q: 如何修改定时任务频率？
A: 在仪表盘页面点击"定时任务"按钮，修改后保存，然后重启 Celery Beat。

### Q: 新闻分析完成度为 0%？
A: 需要配置 API Key 并启动 Celery Worker，系统会自动分析新闻。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，请提交 Issue。

---

**最后更新**: 2025-11-29  
**版本**: V1.0
