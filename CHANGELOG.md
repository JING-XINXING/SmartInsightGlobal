# Changelog

All notable changes to SmartInsight Global will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-11-29

### Added

#### 新功能
- **全球热点地图** (`/map`)
  - SVG 世界地图可视化
  - 新闻地理位置聚合显示
  - 按分类筛选
  - 聚合视图 / 散点视图切换
  - 热点地区排行榜
  - 情感指标颜色编码
  
- **事件时间轴** (`/events`)
  - 基于关键词相似度的事件聚类算法
  - 可折叠的事件卡片
  - 热门话题排行
  - 按时间范围筛选 (3/7/14/30天)
  - 按分类筛选
  
- **新闻详情页** (`/news/[id]`)
  - 完整新闻内容展示
  - AI 分析结果卡片 (情感/分类/来源)
  - 关键词标签
  - 情感分数可视化进度条
  
- **全文搜索** (`/search`)
  - PostgreSQL Full Text Search 索引
  - 标题/内容/关键词搜索
  - 搜索结果分页
  - 搜索历史支持
  
- **数据备份系统** (`scripts/backup/`)
  - `backup_local.sh` - 本地数据库备份脚本
  - `backup_upload.py` - 云端同步脚本 (支持 OSS/S3)
  - `restore.sh` - 数据库恢复脚本
  - Celery 定时备份任务 (每日凌晨2点)
  
- **地理位置提取**
  - AI 自动提取新闻地理位置
  - 支持国家/城市/经纬度
  - `backfill_locations.py` 历史数据补充脚本

#### API 新增
- `GET /api/v1/news/search` - 全文搜索
- `GET /api/v1/map/news-locations` - 获取带位置的新闻
- `GET /api/v1/map/clusters` - 获取位置聚合数据
- `GET /api/v1/map/stats` - 地图统计数据
- `GET /api/v1/events/timeline` - 事件时间轴
- `GET /api/v1/events/trending-topics` - 热门话题

#### 前端组件
- `NewsMap.tsx` - 全球热点地图组件
- `EventTimeline.tsx` - 事件时间轴组件
- `SearchBar.tsx` - 搜索栏组件

### Changed
- Dashboard 数据获取限制从 200 改为 2000，显示全部新闻
- Worker 默认启用地理位置提取 (`extract_location=True`)
- 首页导航栏增加「热点地图」「事件轴」入口

### Fixed
- 无

### Known Issues
- 地图仅显示简化的大陆轮廓，非精确地图
- 已分析的历史新闻需要运行 `backfill_locations.py` 补充位置数据
- 事件聚类基于简单的关键词相似度算法，可能不够精确

---

## [1.0.0] - 2025-11-28

### Added

#### 核心功能
- **新闻采集引擎**
  - 支持 17+ 国际主流媒体 RSS 源
  - 异步并发采集
  - 自动去重
  
- **AI 智能分析**
  - 情感分析 (-100 到 100)
  - 关键词提取 (3-5个)
  - 新闻分类 (12个预定义类别)
  - 统一 LLM 客户端 (支持 6 大厂商)
  
- **数据可视化仪表盘** (`/dashboard`)
  - 核心指标卡片
  - 情感分布饼图
  - 新闻分类柱状图
  - 来源分布图
  - 热门关键词列表
  
- **首页新闻列表**
  - 分页浏览 (20/30/50篇)
  - 来源/分类标签
  - 情感分数显示
  
- **LLM 模型选择器**
  - 厂商选择下拉框
  - 模型选择下拉框
  - 实时配置保存
  
- **定时任务配置**
  - Web 界面配置采集/分析频率
  - Redis 持久化存储

#### API 端点
- `GET /api/v1/news/` - 新闻列表
- `GET /api/v1/news/paginated` - 分页新闻
- `GET /api/v1/news/{id}` - 新闻详情
- `GET /api/v1/llm/providers` - LLM 厂商列表
- `GET /api/v1/llm/models/{provider}` - 厂商模型列表
- `POST /api/v1/llm/update-config` - 更新 LLM 配置
- `GET/POST /api/v1/scheduler/config` - 调度器配置

#### 基础设施
- FastAPI 后端框架
- Next.js 16 前端 (App Router)
- PostgreSQL 数据库 + Alembic 迁移
- Redis 缓存 + Celery 任务队列
- 完整的日志系统

### Changed
- 无 (初始版本)

### Fixed
- 无 (初始版本)

---

## [0.1.0] - 2025-11-27

### Added
- 项目初始化
- 基础架构搭建
- RSS 采集模块原型
- 数据库模型设计

---

## 版本规划

### V1.2 (计划中)
- [ ] PWA 移动端支持
- [ ] AI 日报/周报生成
- [ ] 高级筛选功能
- [ ] 用户认证系统

### V2.0 (远期规划)
- [ ] 多语言支持 (i18n)
- [ ] 实时推送通知
- [ ] 自定义 RSS 源管理
- [ ] 性能优化 (Redis 缓存层)

