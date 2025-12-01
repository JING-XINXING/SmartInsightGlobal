# SmartInsight Global (智察全球)

> 智能全球情报分析系统 - 实时采集、分析和解读全球资讯

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-16-black.svg)
![Status](https://img.shields.io/badge/status-V1.1%20Released-green.svg)

## 📖 项目简介

SmartInsight Global 是一个智能化的全球资讯采集与分析平台，通过整合多个国际主流媒体的 RSS 源，实时获取全球新闻动态，并集成国产大模型进行深度分析。

### 核心特性

- 🌍 **全球视野**: 聚合 BBC、The Guardian、NYT、Al Jazeera、Reuters 等 17+ 主流媒体
- 🤖 **智能分析**: 已集成 DeepSeek/Qwen/Moonshot/智谱/百川/MiniMax 等 6 大国产 LLM
- 📊 **情感分析**: 自动分析新闻情感倾向 (-100 到 100)
- 🏷️ **关键词提取**: AI 自动提取 3-5 个关键词
- 📑 **智能分类**: 12 个预定义类别自动分类
- 📈 **数据可视化**: 仪表盘展示情感分布、分类统计、热门关键词
- 🗺️ **全球热点地图**: 新闻地理位置可视化 (V1.1 新增)
- 📅 **事件时间轴**: 事件聚类与发展脉络 (V1.1 新增)
- 🔍 **全文搜索**: PostgreSQL 全文检索 (V1.1 新增)
- 💾 **数据备份**: 自动备份与云端同步 (V1.1 新增)
- ⏰ **定时任务**: 可配置的自动采集和分析频率
- 📄 **分页浏览**: 支持分页查看新闻列表
- ⚡ **高性能**: 异步架构，Celery 定时任务，Redis 缓存

## 🏗️ 技术架构

### 后端
- **框架**: FastAPI (Python 3.9+)
- **数据库**: PostgreSQL 15 (支持全文搜索)
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

| 页面 | 地址 | 说明 |
|------|------|------|
| 首页 | http://localhost:3000 | 新闻列表（分页） |
| 热点地图 | http://localhost:3000/map | 全球新闻地理分布 |
| 事件时间轴 | http://localhost:3000/events | 事件聚类与脉络 |
| 搜索 | http://localhost:3000/search | 全文搜索 |
| 数据分析 | http://localhost:3000/dashboard | 可视化仪表盘 |
| API 文档 | http://localhost:8000/docs | Swagger API 文档 |

## 📁 项目结构

```
SmartInsightGlobal/
├── backend/                     # 后端服务
│   ├── app/
│   │   ├── api/api_v1/endpoints/
│   │   │   ├── news.py         # 新闻 API (分页、搜索、详情)
│   │   │   ├── llm.py          # LLM 配置 API
│   │   │   ├── scheduler.py    # 定时任务配置 API
│   │   │   ├── map.py          # 地图数据 API (V1.1)
│   │   │   └── events.py       # 事件时间轴 API (V1.1)
│   │   ├── core/
│   │   │   ├── analyzer.py     # AI 分析引擎 (含地理位置提取)
│   │   │   ├── llm_client.py   # 统一 LLM 客户端
│   │   │   └── scheduler_config.py
│   │   └── worker.py           # Celery 任务
│   ├── alembic/versions/       # 数据库迁移
│   │   ├── f56b995b94be_initial_migration.py
│   │   ├── 56c2fcd4793d_add_fulltext_search_index.py
│   │   └── ff7e7a245174_add_location_field.py
│   ├── backfill_locations.py   # 位置数据补充脚本
│   └── logs/
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # 首页
│   │   ├── dashboard/          # 数据分析仪表盘
│   │   ├── map/                # 全球热点地图 (V1.1)
│   │   ├── events/             # 事件时间轴 (V1.1)
│   │   ├── search/             # 搜索页面 (V1.1)
│   │   └── news/[id]/          # 新闻详情页 (V1.1)
│   └── components/
│       ├── Dashboard.tsx
│       ├── NewsMap.tsx         # 地图组件 (V1.1)
│       ├── EventTimeline.tsx   # 时间轴组件 (V1.1)
│       ├── SearchBar.tsx       # 搜索栏 (V1.1)
│       ├── LLMSelector.tsx
│       └── SchedulerSettings.tsx
├── scripts/backup/              # 备份脚本 (V1.1)
│   ├── backup_local.sh
│   ├── backup_upload.py
│   ├── restore.sh
│   └── config.example.yaml
├── docs/                        # 文档
├── CHANGELOG.md                 # 版本变更日志
└── docker-compose.yml
```

## 📊 功能说明

### 首页 - 新闻列表
- 分页浏览新闻 (每页 20/30/50 篇可选)
- 显示新闻标题、来源、时间、分类、情感分数
- 显示 AI 提取的关键词标签
- 快速入口: 热点地图、事件轴、数据分析

### 全球热点地图 (V1.1 新增)
- SVG 世界地图可视化
- 新闻按地理位置聚合显示
- 情感指标颜色编码 (正面/中性/负面)
- 热点地区排行榜
- 支持按分类筛选

### 事件时间轴 (V1.1 新增)
- 基于关键词相似度的事件聚类
- 可折叠的事件卡片
- 事件发展脉络展示
- 热门话题排行
- 支持时间范围筛选 (3/7/14/30天)

### 全文搜索 (V1.1 新增)
- PostgreSQL Full Text Search
- 标题、内容、关键词搜索
- 搜索结果分页
- 高亮匹配内容

### 数据分析仪表盘
- **AI 模型选择**: 选择 LLM 厂商和具体模型
- **定时任务设置**: 配置采集和分析频率
- **核心指标卡片**: 总文章数、平均情感、风险指数、分析完成度
- **可视化图表**: 情感分布、新闻分类、来源分布、热门关键词

### 数据备份 (V1.1 新增)
- 本地 PostgreSQL 备份 (pg_dump + gzip)
- 云端同步支持 (阿里云 OSS / AWS S3)
- Celery 定时任务 (每日凌晨2点自动备份)
- 一键恢复脚本

## 📡 API 端点

### 新闻相关
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/news/` | GET | 获取新闻列表 |
| `/api/v1/news/paginated` | GET | 分页获取新闻 |
| `/api/v1/news/search` | GET | 全文搜索 (V1.1) |
| `/api/v1/news/{id}` | GET | 获取新闻详情 |

### LLM 配置
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/llm/providers` | GET | 获取 LLM 厂商列表 |
| `/api/v1/llm/models/{provider}` | GET | 获取厂商模型列表 |
| `/api/v1/llm/update-config` | POST | 更新 LLM 配置 |

### 地图与事件 (V1.1 新增)
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/map/news-locations` | GET | 获取带位置的新闻 |
| `/api/v1/map/clusters` | GET | 获取位置聚合数据 |
| `/api/v1/map/stats` | GET | 地图统计数据 |
| `/api/v1/events/timeline` | GET | 事件时间轴 |
| `/api/v1/events/trending-topics` | GET | 热门话题 |

### 调度器
| 端点 | 方法 | 说明 |
|------|------|------|
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

### ✅ V1.1 阶段 (100% 完成)
- [x] 新闻详情页
- [x] 全文搜索
- [x] 全球热点地图
- [x] 事件时间轴
- [x] 地理位置提取
- [x] 数据备份系统

### 🚧 V1.2 阶段 (计划中)
- [ ] PWA 移动端支持
- [ ] AI 日报/周报生成
- [ ] 高级筛选功能
- [ ] 新闻收藏功能
- [ ] 数据导出 (CSV/Excel)

### 📋 V2.0 阶段 (远期规划)
- [ ] 用户认证系统
- [ ] 多语言支持 (i18n)
- [ ] 实时推送通知
- [ ] 自定义 RSS 源管理
- [ ] 性能优化 (Redis 缓存层)

## 🔧 常见问题

### Q: 为什么 LLM 厂商显示"未配置"？
A: 确保在 `.env` 文件中配置了对应厂商的 API Key，然后重启后端服务。

### Q: 如何修改定时任务频率？
A: 在仪表盘页面点击"定时任务"按钮，修改后保存，然后重启 Celery Beat。

### Q: 新闻分析完成度为 0%？
A: 需要配置 API Key 并启动 Celery Worker，系统会自动分析新闻。

### Q: 地图显示"暂无地理位置数据"？
A: 已分析的历史新闻需要运行位置补充脚本：
```bash
cd backend
python backfill_locations.py --limit 200
```

### Q: 如何手动触发数据备份？
A: 运行备份脚本：
```bash
cd scripts/backup
./backup_local.sh
```

## 📝 版本历史

查看 [CHANGELOG.md](./CHANGELOG.md) 了解详细的版本变更记录。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，请提交 Issue。

---

**最后更新**: 2025-11-29  
**版本**: V1.1
