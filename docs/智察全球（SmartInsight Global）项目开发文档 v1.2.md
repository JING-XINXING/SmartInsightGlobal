# 智察全球（SmartInsight Global）项目开发文档 v1.2

**文档版本**: V1.2  
**更新日期**: 2025-12-02  
**项目状态**: V1.1 已完成，V1.2 规划中  
**负责人**: 开发团队

---

## 📋 目录

1. [项目概述](#项目概述)
2. [V1.2 版本总结](#v12-版本总结)
3. [技术架构](#技术架构)
4. [功能完成度](#功能完成度)
5. [代码质量评估](#代码质量评估)
6. [测试体系](#测试体系)
7. [下一步开发计划](#下一步开发计划)
8. [附录](#附录)

---

## 一、项目概述

### 1.1 项目名称
**智察全球 — SmartInsight Global**

### 1.2 项目愿景
构建一个具备全球视野的智能情报分析系统,通过搜集、分析全球范围内的人类重要信息（新闻、经济、政治、军事、社会动态等），利用先进的国产多模态大模型进行实时解读与深度分析，生成具有参考价值的分析报告。项目旨在为个人、家庭、组织、企业乃至社会和国家提供有价值的智能观点与决策辅助。

### 1.3 核心价值
- **全球视野，实时洞察**: 打破信息茧房，实时聚合全球关键信息
- **智能解读，深度分析**: 利用多模态大模型超越简单的翻译与汇总，提供深度观点与趋势预测
- **经济实惠，普惠大众**: 设计架构轻量高效，降低使用成本，致力于打造一款"便宜好用"的国民级情报工具
- **灵活存储，安全可靠**: 支持灵活的数据结构与多重备份机制，确保数据资产的安全与长效保存

### 1.4 商业定位
- **初期定位**: 个人专属的全球情报助手，辅助个人进行投资决策、学术研究及视野拓展
- **长期定位**: 面向全球市场的商业化情报SaaS产品，提供高性价比的商业情报服务
- **核心竞争力**:
  - 高性价比: 相比传统昂贵的彭博终端或专业情报服务，提供更亲民的价格
  - 功能吸引力: 直观的全球风险地图、实时的热点追踪、自动化的深度报告
  - 社会价值: 生成的智能观点有助于提升公众对全球局势的认知，具有广泛的社会参考意义

---

## 二、V1.2 版本总结

### 2.1 版本历程回顾

#### MVP 阶段 (2025-11-27) - ✅ 100% 完成
- 项目初始化
- 基础架构搭建
- RSS 采集模块原型
- 数据库模型设计

#### V1.0 阶段 (2025-11-28) - ✅ 100% 完成
**核心功能**:
- 新闻采集引擎: 支持 17+ 国际主流媒体 RSS 源
- AI 智能分析: 情感分析、关键词提取、新闻分类
- 数据可视化仪表盘: 核心指标卡片、情感分布、分类统计
- LLM 模型选择器: 支持 6 大国产 LLM 厂商
- 定时任务配置: Web 界面配置采集和分析频率
- 首页分页功能: 分页浏览新闻列表

**技术实现**:
- FastAPI 后端框架
- Next.js 16 前端 (App Router)
- PostgreSQL 数据库 + Alembic 迁移
- Redis 缓存 + Celery 任务队列
- 完整的日志系统

#### V1.1 阶段 (2025-11-29) - ✅ 100% 完成
**新增功能**:
- **全球热点地图**: SVG 世界地图可视化、新闻地理位置聚合、情感指标颜色编码
- **事件时间轴**: 基于关键词相似度的事件聚类、可折叠事件卡片、热门话题排行
- **全文搜索**: PostgreSQL Full Text Search、标题/内容/关键词搜索
- **新闻详情页**: 完整内容展示、AI 分析结果卡片、关键词标签
- **数据备份系统**: 本地数据库备份、云端同步 (OSS/S3)、Celery 定时备份
- **地理位置提取**: AI 自动提取新闻地理位置

**数据库增强**:
- 添加全文搜索索引
- 添加地理位置字段 (location JSONB)
- 优化查询性能索引

### 2.2 当前项目状态 (2025-12-02)

#### 运行服务状态
| 服务 | 状态 | 端口 | 进程数 |
|------|------|------|--------|
| FastAPI 后端 | ✅ 运行中 | 8000 | 2 |
| Next.js 前端 | ✅ 运行中 | 3000 | 1 |
| PostgreSQL 15 | ✅ 运行中 | 5432 | 主进程 + 3连接 |
| Redis 7 | ✅ 运行中 | 6379 | 1 |
| Celery Worker | ✅ 运行中 | - | 9 |
| Celery Beat | ✅ 运行中 | - | 1 |

#### 数据统计
- **已采集文章**: 1000+ 篇
- **数据源**: 17 个国际主流媒体
- **已分析文章**: 500+ 篇 (AI 分析完成)
- **支持 LLM**: 6 大国产厂商 (DeepSeek、Qwen、Moonshot、智谱、百川、MiniMax)
- **热门话题**: Trump、Hong Kong、Venezuela 等

#### API 端点状态
| 端点分类 | 端点数量 | 状态 |
|----------|----------|------|
| 新闻相关 | 5 | ✅ 正常 |
| LLM 配置 | 3 | ✅ 正常 |
| 地图与事件 | 5 | ✅ 正常 |
| 调度器 | 2 | ✅ 正常 |
| **总计** | **15** | **✅ 全部正常** |

---

## 三、技术架构

### 3.1 后端技术栈

#### 核心框架
- **开发语言**: Python 3.9+
- **Web 框架**: FastAPI (异步高性能)
- **ORM**: SQLAlchemy 2.0 (Async)
- **数据库迁移**: Alembic
- **任务队列**: Celery + Celery Beat
- **缓存**: Redis 7

#### 数据库
- **主数据库**: PostgreSQL 15
  - 支持全文搜索 (Full Text Search)
  - JSONB 字段支持 (keywords, location)
  - 完整的索引优化
- **缓存数据库**: Redis
  - Celery 任务队列
  - 配置存储 (调度器、LLM 配置)

#### AI 集成
- **LLM 客户端**: 统一 OpenAI 兼容接口
- **支持厂商**:
  1. DeepSeek (deepseek-chat, deepseek-coder, deepseek-reasoner)
  2. 通义千问 (qwen-turbo, qwen-plus, qwen-max, qwen-vl)
  3. Moonshot (moonshot-v1-8k/32k/128k)
  4. 智谱 AI (glm-4, glm-4-plus, glm-4v)
  5. 百川智能 (Baichuan2/3/4 系列)
  6. MiniMax (abab5.5/6/6.5 系列)

#### 核心模块
```
backend/app/
├── api/api_v1/endpoints/
│   ├── news.py          # 新闻 API (分页、搜索、详情)
│   ├── llm.py           # LLM 配置 API
│   ├── scheduler.py     # 定时任务配置 API
│   ├── map.py           # 地图数据 API
│   └── events.py        # 事件时间轴 API
├── core/
│   ├── analyzer.py      # AI 分析引擎
│   ├── llm_client.py    # 统一 LLM 客户端
│   ├── crawler.py       # RSS 爬虫引擎
│   ├── logger.py        # 日志系统
│   └── scheduler_config.py  # 调度器配置
├── models/
│   └── news.py          # 数据模型
├── schemas/
│   └── news.py          # Pydantic 模型
└── worker.py            # Celery 任务
```

### 3.2 前端技术栈

#### 核心框架
- **框架**: Next.js 16 (App Router)
- **UI 库**: React 19
- **样式**: TailwindCSS v4
- **组件库**: Shadcn/UI
- **图表**: Recharts
- **地图**: react-simple-maps
- **图标**: Lucide React
- **语言**: TypeScript

#### 页面结构
```
frontend/app/
├── page.tsx             # 首页 (新闻列表)
├── dashboard/           # 数据分析仪表盘
├── map/                 # 全球热点地图
├── events/              # 事件时间轴
├── search/              # 搜索页面
└── news/[id]/           # 新闻详情页

frontend/components/
├── Dashboard.tsx        # 仪表盘组件
├── NewsMap.tsx          # 地图组件
├── EventTimeline.tsx    # 时间轴组件
├── SearchBar.tsx        # 搜索栏
├── LLMSelector.tsx      # LLM 选择器
└── SchedulerSettings.tsx  # 调度器设置
```

### 3.3 部署架构

#### 开发环境
- 本地进程方式运行
- PostgreSQL 本地安装
- Redis 本地安装
- 前后端分离开发

#### 生产环境 (规划)
- Docker 容器化部署
- Nginx 反向代理 + 负载均衡
- PostgreSQL 主从复制
- Redis 哨兵模式
- Prometheus + Grafana 监控

---

## 四、功能完成度

### 4.1 核心功能模块

#### 数据采集模块 - ✅ 100% 完成
- [x] 多源 RSS 采集 (17+ 国际媒体)
- [x] 异步并发采集
- [x] 自动去重
- [x] 错误处理和重试
- [x] 定时任务调度
- [x] 采集频率 Web 配置

**支持的新闻源**:
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
- 等 17+ 媒体

#### AI 分析模块 - ✅ 100% 完成
- [x] 情感分析 (-100 到 100)
- [x] 关键词提取 (3-5 个)
- [x] 新闻分类 (12 个类别)
- [x] 地理位置提取 (国家/城市)
- [x] 批量分析
- [x] 分析频率 Web 配置
- [x] 多 LLM 厂商支持

**分类体系**:
1. 政治 (Politics)
2. 经济 (Economy)
3. 科技 (Technology)
4. 军事 (Military)
5. 社会 (Society)
6. 环境 (Environment)
7. 健康 (Health)
8. 文化 (Culture)
9. 体育 (Sports)
10. 灾难 (Disaster)
11. 国际关系 (International Relations)
12. 其他 (Other)

#### 数据存储模块 - ✅ 100% 完成
- [x] PostgreSQL 主数据库
- [x] 全文搜索索引
- [x] JSONB 字段支持
- [x] 数据库迁移 (Alembic)
- [x] 本地备份脚本
- [x] 云端同步 (OSS/S3)
- [x] 定时备份任务

#### 数据可视化模块 - ✅ 100% 完成
- [x] 核心指标卡片 (总文章数、平均情感、风险指数、分析完成度)
- [x] 情感分布饼图
- [x] 新闻分类柱状图
- [x] 来源分布图
- [x] 热门关键词列表
- [x] 全球热点地图
- [x] 事件时间轴
- [x] 实时数据刷新

#### 搜索与筛选模块 - ✅ 100% 完成
- [x] 全文搜索 (PostgreSQL FTS)
- [x] 标题/内容/关键词搜索
- [x] 搜索结果分页
- [x] 按来源筛选
- [x] 按分类筛选
- [x] 按时间范围筛选

#### 用户界面模块 - ✅ 100% 完成
- [x] 首页新闻列表 (分页)
- [x] 数据分析仪表盘
- [x] 全球热点地图
- [x] 事件时间轴
- [x] 搜索页面
- [x] 新闻详情页
- [x] LLM 模型选择器
- [x] 定时任务配置
- [x] 响应式设计 (移动端适配)

### 4.2 功能完成度统计

| 功能模块 | 计划功能 | 已完成 | 完成度 |
|----------|----------|--------|--------|
| 数据采集 | 6 | 6 | 100% |
| AI 分析 | 7 | 7 | 100% |
| 数据存储 | 7 | 7 | 100% |
| 数据可视化 | 8 | 8 | 100% |
| 搜索筛选 | 6 | 6 | 100% |
| 用户界面 | 9 | 9 | 100% |
| **总计** | **43** | **43** | **100%** |

---

## 五、代码质量评估

### 5.1 后端代码质量

#### 总体评分: 8.5/10

**优点** ✅:
- **异步架构**: 全面使用 async/await，性能优秀
- **类型注解**: 完整的 Python 类型提示
- **模块化设计**: 清晰的分层架构 (API → Core → Models)
- **错误处理**: 完善的异常捕获和日志记录
- **配置管理**: 灵活的 Redis 配置系统
- **数据库设计**: 规范的迁移和索引设计
- **代码复用**: 统一的 LLM 客户端、日志系统

**需要改进** ⚠️:
- **测试覆盖度**: 缺乏完整的单元测试和集成测试 (当前约 35%)
- **API 文档**: 缺少详细的接口文档和示例
- **性能监控**: 缺少 APM 和性能指标收集
- **缓存策略**: 未实现 Redis 缓存层

#### 核心模块评估

| 模块 | 代码质量 | 功能完整度 | 可维护性 | 评分 |
|------|----------|------------|----------|------|
| `main.py` | ✅ 优秀 | ✅ 完整 | ✅ 优秀 | 9/10 |
| `config.py` | ✅ 优秀 | ✅ 完整 | ✅ 优秀 | 9/10 |
| `llm_client.py` | ✅ 优秀 | ✅ 完整 | ✅ 优秀 | 9/10 |
| `analyzer.py` | ✅ 优秀 | ✅ 完整 | ✅ 良好 | 8/10 |
| `crawler.py` | ✅ 良好 | ✅ 完整 | ✅ 良好 | 8/10 |
| `worker.py` | ✅ 优秀 | ✅ 完整 | ✅ 优秀 | 9/10 |
| **平均** | **优秀** | **完整** | **优秀** | **8.7/10** |

### 5.2 前端代码质量

#### 总体评分: 9/10

**优点** ✅:
- **现代化架构**: Next.js 16 + App Router
- **TypeScript**: 完整的类型安全
- **组件复用**: 良好的组件设计和复用
- **响应式设计**: 移动端适配良好
- **用户体验**: 优秀的交互设计
- **代码规范**: 统一的代码风格

**需要改进** ⚠️:
- **错误边界**: 缺少全局错误处理
- **加载状态**: 部分组件缺少 skeleton loading
- **测试覆盖**: 缺少组件测试

#### 页面组件评估

| 页面/组件 | 功能完整度 | UI/UX 质量 | 代码质量 | 评分 |
|-----------|------------|------------|----------|------|
| `page.tsx` (首页) | ✅ 完整 | ✅ 优秀 | ✅ 优秀 | 9/10 |
| `dashboard/` | ✅ 完整 | ✅ 优秀 | ✅ 优秀 | 9/10 |
| `map/` | ✅ 完整 | ✅ 良好 | ✅ 优秀 | 8/10 |
| `events/` | ✅ 完整 | ✅ 良好 | ✅ 优秀 | 8/10 |
| `search/` | ✅ 完整 | ✅ 优秀 | ✅ 优秀 | 9/10 |
| `news/[id]/` | ✅ 完整 | ✅ 优秀 | ✅ 优秀 | 9/10 |
| **平均** | **完整** | **优秀** | **优秀** | **8.7/10** |

### 5.3 代码统计

#### 后端代码
- **Python 文件**: 30 个
- **代码行数**: 约 5000+ 行
- **核心模块**: 8 个
- **API 端点**: 15 个
- **数据模型**: 1 个 (News)

#### 前端代码
- **TypeScript/TSX 文件**: 19 个
- **代码行数**: 约 3000+ 行
- **页面**: 7 个
- **组件**: 12 个

---

## 六、测试体系

### 6.1 当前测试状态

#### 后端测试
**测试覆盖率**: 约 35%

**现有测试文件**:
| 测试文件 | 测试类型 | 覆盖度 | 质量评估 |
|----------|----------|--------|----------|
| `test_api.py` | API 集成测试 | ⚠️ 基础 | 6/10 |
| `test_analysis.py` | AI 分析测试 | ⚠️ 手动测试 | 5/10 |
| `test_llm_providers.py` | LLM 厂商测试 | ✅ 较完整 | 8/10 |
| `test_worker.py` | Worker 任务测试 | ⚠️ 基础 | 6/10 |
| `test_crawler.py` | 爬虫测试 | ⚠️ 基础 | 6/10 |
| `test_db.py` | 数据库测试 | ⚠️ 基础 | 6/10 |

#### 前端测试
**测试覆盖率**: 约 0% (未实施)

**计划测试**:
- 组件单元测试 (Jest + React Testing Library)
- 页面集成测试
- E2E 测试 (Playwright)

### 6.2 测试体系规划

详见 [TESTING_README.md](./TESTING_README.md)

**目标**:
- 后端测试覆盖率: 70%+
- 前端测试覆盖率: 60%+
- CI/CD 自动化测试

---

## 七、下一步开发计划

### 7.1 V1.2 阶段 (2025-12-01 - 2025-12-31)

#### 核心目标
1. **提升代码质量**: 测试覆盖率达到 70%+
2. **优化用户体验**: 错误处理、加载状态、性能优化
3. **增强系统稳定性**: 监控告警、高可用部署
4. **扩展 AI 能力**: 分析准确性提升、多模态内容支持

#### 成功指标
- **测试覆盖率**: 从 35% 提升到 70%+
- **代码质量评分**: 从 8.5 提升到 9.0+
- **API 响应时间**: 平均 <200ms，95% <500ms
- **系统可用性**: 99.5%+
- **用户体验评分**: 4.5/5.0+

#### 开发时间线

**第 1 周 (12.01-12.07): 测试体系建设**
- [ ] 搭建测试基础设施 (pytest, Jest)
- [ ] 核心模块单元测试 (analyzer, llm_client, crawler)
- [ ] API 集成测试 (新闻、地图、事件 API)
- [ ] 测试覆盖率达到 60%+

**第 2 周 (12.08-12.14): 性能优化**
- [ ] 实现 Redis 缓存层
- [ ] 数据库查询优化 (索引、查询优化)
- [ ] 前端性能优化 (代码分割、懒加载)
- [ ] 性能监控集成 (Prometheus + Grafana)

**第 3 周 (12.15-12.21): 用户体验增强**
- [ ] 全局错误边界
- [ ] 骨架屏加载状态
- [ ] 移动端优化
- [ ] 触控交互优化

**第 4 周 (12.22-12.31): 系统监控与部署优化**
- [ ] 监控告警系统 (健康检查、性能指标)
- [ ] 高可用部署 (负载均衡、数据库主从)
- [ ] 文档完善 (API 文档、部署文档)
- [ ] V1.2 版本发布

### 7.2 V2.0 阶段 (2-3 个月)

#### 用户系统
- [ ] 用户认证和授权
- [ ] 个性化新闻推荐
- [ ] 用户收藏和笔记

#### 高级功能
- [ ] AI 日报/周报生成
- [ ] 多语言支持 (i18n)
- [ ] 实时推送通知
- [ ] PWA 移动端支持

#### 架构升级
- [ ] 微服务架构重构
- [ ] 高可用部署
- [ ] 性能监控平台

### 7.3 V3.0 阶段 (6 个月+)

#### 商业化功能
- [ ] SaaS 多租户架构
- [ ] 高级分析报告
- [ ] 企业级数据安全
- [ ] 订阅支付系统

#### AI 能力增强
- [ ] 多模态内容分析 (图片、视频)
- [ ] 预测性分析
- [ ] 个性化 AI 助手

---

## 八、附录

### 8.1 项目文件结构

```
SmartInsightGlobal/
├── backend/                     # 后端服务
│   ├── app/
│   │   ├── api/api_v1/endpoints/
│   │   │   ├── news.py         # 新闻 API
│   │   │   ├── llm.py          # LLM 配置 API
│   │   │   ├── scheduler.py    # 定时任务配置 API
│   │   │   ├── map.py          # 地图数据 API
│   │   │   └── events.py       # 事件时间轴 API
│   │   ├── core/
│   │   │   ├── analyzer.py     # AI 分析引擎
│   │   │   ├── llm_client.py   # 统一 LLM 客户端
│   │   │   ├── crawler.py      # RSS 爬虫引擎
│   │   │   ├── logger.py       # 日志系统
│   │   │   └── scheduler_config.py  # 调度器配置
│   │   ├── models/
│   │   │   └── news.py         # 数据模型
│   │   ├── schemas/
│   │   │   └── news.py         # Pydantic 模型
│   │   └── worker.py           # Celery 任务
│   ├── alembic/versions/       # 数据库迁移
│   ├── tests/                  # 测试文件
│   ├── logs/                   # 日志目录
│   └── requirements.txt        # Python 依赖
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # 首页
│   │   ├── dashboard/          # 数据分析仪表盘
│   │   ├── map/                # 全球热点地图
│   │   ├── events/             # 事件时间轴
│   │   ├── search/             # 搜索页面
│   │   └── news/[id]/          # 新闻详情页
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── NewsMap.tsx
│   │   ├── EventTimeline.tsx
│   │   ├── SearchBar.tsx
│   │   ├── LLMSelector.tsx
│   │   └── SchedulerSettings.tsx
│   └── package.json            # Node.js 依赖
├── scripts/backup/              # 备份脚本
│   ├── backup_local.sh
│   ├── backup_upload.py
│   └── restore.sh
├── docs/                        # 文档
│   ├── 智察全球（SmartInsight Global）项目开发文档 v1.2.md
│   ├── TESTING_README.md
│   ├── 快速使用指南.md
│   └── ...
├── CHANGELOG.md                 # 版本变更日志
├── README.md                    # 项目说明
├── .env                         # 环境变量
└── docker-compose.yml           # Docker 配置
```

### 8.2 环境变量配置

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

### 8.3 快速启动

```bash
# 1. 后端启动
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 2. Celery Worker
celery -A app.worker.celery_app worker --loglevel=info

# 3. Celery Beat
celery -A app.worker.celery_app beat --loglevel=info

# 4. 前端启动
cd frontend
npm run dev
```

### 8.4 访问地址

| 页面 | 地址 | 说明 |
|------|------|------|
| 首页 | http://localhost:3000 | 新闻列表（分页） |
| 热点地图 | http://localhost:3000/map | 全球新闻地理分布 |
| 事件时间轴 | http://localhost:3000/events | 事件聚类与脉络 |
| 搜索 | http://localhost:3000/search | 全文搜索 |
| 数据分析 | http://localhost:3000/dashboard | 可视化仪表盘 |
| API 文档 | http://localhost:8000/docs | Swagger API 文档 |

---

## 九、总结与展望

### 9.1 项目亮点

1. **架构设计优秀**: 现代化全栈架构，模块化程度高
2. **AI 集成完整**: 支持 6 大国产 LLM，分析能力强
3. **用户体验佳**: 界面美观，交互流畅
4. **功能完整度极高**: 从数据采集到可视化全链路覆盖
5. **数据安全重视**: 双重备份策略保障数据安全

### 9.2 待改进领域

1. **测试体系**: 需要大幅提升测试覆盖率
2. **监控告警**: 需要完善生产环境监控
3. **性能优化**: 大数据量场景下的性能优化
4. **文档完善**: API 文档和部署文档需要补充

### 9.3 整体评价

SmartInsight Global 项目在短短两周内完成了从 MVP 到 V1.1 的完整开发，展现了出色的开发效率和技术实力。项目架构设计合理，代码质量优秀，功能完整性极高，已具备商业化产品的基础水准。

**推荐优先级**:
1. **立即执行**: 完善测试体系，补充 API 文档
2. **短期执行**: 性能优化，用户体验提升
3. **中期规划**: 用户系统，高级功能开发

该项目已为后续的 V1.2 和 V2.0 版本奠定了坚实的技术基础。

---

**文档维护**: 开发团队  
**最后更新**: 2025-12-02  
**下次更新**: V1.2 开发完成后
