# SmartInsight Global V2.0 版本升级计划

**项目名称**: SmartInsight Global（智察全球）  
**当前版本**: V1.5.0  
**目标版本**: V2.0.0  
**编写日期**: 2026-11-25  
**文档版本**: 1.0

---

## 一、项目现状分析

### 1.1 项目概览

SmartInsight Global 是一个智能化的全球资讯采集与分析平台，当前版本 V1.5.0 已实现：
- 17+ 国际主流媒体 RSS 新闻采集
- 6 大国产 LLM 智能分析引擎（DeepSeek/Qwen/Moonshot/智谱/百川/MiniMax）
- 情感分析、关键词提取、智能分类
- 全球热点地图（70+ 国家坐标映射）
- JWT 认证 + RBAC 权限控制
- 用户偏好设置、分析历史管理
- Celery 定时任务调度

### 1.2 技术栈现状

| 层次 | 技术 | 版本 | 状态 |
|------|------|------|------|
| 后端框架 | FastAPI | 最新 | ✅ 良好 |
| 数据库 | PostgreSQL | 15 | ✅ 良好 |
| 缓存 | Redis | 7 | ✅ 良好 |
| ORM | SQLAlchemy (Async) | 2.x | ✅ 良好 |
| 任务队列 | Celery + Beat | 5.x | ✅ 良好 |
| 前端框架 | Next.js | 16 | ⚠️ 前端目录为空 |
| UI 组件 | Shadcn/UI + TailwindCSS v4 | - | ⚠️ 未实际部署 |
| 移动端 | React Native | 0.72 | ⚠️ 仅骨架代码 |
| CI/CD | GitHub Actions | - | ⚠️ 配置存在但未完善 |

### 1.3 代码规模统计

| 模块 | 文件数 | 代码行数 | 说明 |
|------|--------|----------|------|
| 后端核心 (app/) | ~40 | ~17,500 | 主要业务逻辑 |
| 后端测试 (tests/) | ~15 | ~3,200 | 测试套件 |
| 移动端骨架 (mobile/) | ~12 | ~1,000 | 仅有骨架组件 |
| 配置/脚本 | ~10 | ~800 | Docker、CI/CD、备份脚本 |
| 文档 | 27 | - | 多个版本的开发文档 |

---

## 二、现有功能详细分析

### 2.1 核心功能评估

#### ✅ 优势功能

| 功能 | 评分 | 说明 |
|------|------|------|
| RSS 新闻采集引擎 | ⭐⭐⭐⭐ | 支持 17+ 源，异步并发采集，自动去重 |
| 多 LLM 统一客户端 | ⭐⭐⭐⭐⭐ | 6 大厂商统一 OpenAI 兼容接口，优秀的抽象设计 |
| 情感分析系统 | ⭐⭐⭐⭐ | 多模型加权分析，细粒度情感识别 |
| 高级 NLP 引擎 | ⭐⭐⭐⭐ | NER、关系抽取、趋势预测一体化 |
| 认证系统 | ⭐⭐⭐⭐ | JWT + RBAC，完整的用户/会话/审计日志 |
| 数据库设计 | ⭐⭐⭐⭐ | 字段丰富，支持全文搜索和 JSONB |
| 定时任务 | ⭐⭐⭐⭐ | Celery 调度，Web 配置界面 |
| 数据备份 | ⭐⭐⭐ | 本地 + 云端双备份策略 |

#### ⚠️ 需要改进

| 功能 | 评分 | 说明 |
|------|------|------|
| 前端应用 | ⭐⭐ | 目录为空，需要完整重建 |
| 移动端 App | ⭐ | 仅骨架代码，React Native 0.72 过时 |
| 测试覆盖率 | ⭐⭐ | ~45% 覆盖率，大量散落的测试文件 |
| API 文档 | ⭐⭐⭐ | Swagger 自动生成，但缺少使用示例 |
| 国际化 | ⭐⭐ | 后端 i18n 模块已就绪，但未充分应用 |
| 实时通知 | ⭐ | 仅有 API 占位符，无 WebSocket |

### 2.2 后端架构分析

#### 优点

1. **模块化设计**：API 路由按功能拆分（news/llm/scheduler/map/events/auth/preferences/analysis），职责清晰
2. **异步架构**：全链路异步 I/O（FastAPI + asyncpg + httpx）
3. **统一 LLM 接口**：`LLMClient` 类设计优雅，支持多厂商切换和 Mock 回退
4. **高级 NLP 分析**：`AdvancedNLPAnalyzer` 支持多模型融合分析（关键词/规则/LLM/情感四模型加权）
5. **完善的用户模型**：User 模型包含角色、权限、会话、访问日志、审计日志
6. **数据库迁移**：Alembic 管理，5 个迁移版本有序演进

#### 不足

1. **数据库连接池**：使用 `NullPool`（无池化），高并发下性能不佳
2. **API 端点重复**：存在 `_simple` 后缀的简化版端点与完整版并存（如 auth_simple.py / auth.py, map_simple.py / map.py），代码冗余
3. **测试文件混乱**：根目录散落着 test_*.py 文件（test_analysis.py, test_api.py, test_db.py 等），应统一到 tests/ 目录
4. **环境变量管理**：依赖文件路径查找 .env，未使用更健壮的配置管理方案
5. **错误处理不统一**：部分端点直接捕获 Exception，缺少全局异常处理中间件
6. **缺少 API 速率限制**：无请求频率控制，易受 DDoS 攻击
7. **LLM 随机选择**：分析任务随机选择 provider，不保证一致性
8. **requirements.txt 无版本锁定**：所有依赖未固定版本号，可能导致构建不可复现

### 2.3 前端状态分析

**严重问题**：`/workspace/frontend/` 目录为空，前端代码完全缺失。

根据 README 文档描述，前端应包含：
- 14+ 页面（首页/登录/注册/地图/时间轴/搜索/仪表盘/分析/报告/个人资料/设置等）
- 多个组件（Dashboard/NewsMap/EventTimeline/SearchBar/LLMSelector 等）

**需要完全重建前端应用。**

### 2.4 移动端状态分析

`/workspace/mobile/` 目录存在基础骨架代码：
- 8 个屏幕组件（NewsListScreen/AuthScreen/MapScreen 等）
- 2 个通用组件（NewsCard/SentimentIndicator）
- API 服务层和类型定义
- 但未安装依赖（无 node_modules），React Native 0.72 已过时

### 2.5 DevOps 和基础设施分析

| 组件 | 状态 | 问题 |
|------|------|------|
| docker-compose.yml | ✅ 基础配置 | 仅包含 db 和 redis |
| docker-compose.production.yml | ✅ 完整 | 包含 backend/celery/frontend/nginx |
| CI/CD (GitHub Actions) | ⚠️ 配置存在 | 引用不存在的 requirements-test.txt 和 scripts |
| Dockerfile (backend) | ❌ 缺失 | docker-compose.production.yml 引用但不存在 |
| Dockerfile (frontend) | ❌ 缺失 | docker-compose.production.yml 引用但不存在 |
| Nginx 配置 | ❌ 缺失 | docker-compose.production.yml 引用但不存在 |
| 环境变量模板 | ✅ 存在 | .env.example 覆盖基本配置 |

---

## 三、关键问题和不足汇总

### 3.1 P0 级问题（阻断性）

| # | 问题 | 影响 | 建议 |
|---|------|------|------|
| 1 | **前端代码缺失** | 无法提供 Web 界面 | 完整重建 Next.js 前端 |
| 2 | **后端 Dockerfile 缺失** | 无法容器化部署 | 编写 Dockerfile 和构建流程 |
| 3 | **依赖版本未锁定** | 构建不可复现 | 锁定 requirements.txt 版本 |
| 4 | **CI/CD 配置引用缺失文件** | 流水线无法运行 | 补全 requirements-test.txt 和测试脚本 |

### 3.2 P1 级问题（重要）

| # | 问题 | 影响 | 建议 |
|---|------|------|------|
| 5 | 数据库连接池使用 NullPool | 高并发性能差 | 切换为 AsyncPool |
| 6 | API 端点代码冗余（_simple 版本） | 维护困难 | 合并重复端点 |
| 7 | 缺少 API 速率限制 | 安全风险 | 引入 slowapi 或自定义限流 |
| 8 | 缺少全局异常处理 | 错误响应不统一 | 添加全局异常处理中间件 |
| 9 | 测试文件组织混乱 | 维护困难 | 统一到 tests/ 目录 |
| 10 | 缺少 WebSocket 实时通知 | 用户体验差 | 实现 WebSocket 推送 |

### 3.3 P2 级问题（改进项）

| # | 问题 | 影响 | 建议 |
|---|------|------|------|
| 11 | LLM 分析随机选择 provider | 结果不一致 | 实现智能路由策略 |
| 12 | 国际化功能未完整 | 国际用户体验 | 完善 i18n 支持 |
| 13 | 文档数量多但内容冗余 | 维护成本 | 精简和合并文档 |
| 14 | 移动端代码过时 | 移动端不可用 | 升级到 Expo/RN 新架构 |
| 15 | 缺少监控和可观测性 | 运维困难 | 引入 Prometheus/Grafana |

---

## 四、V2.0 版本升级计划

### 4.1 版本目标

**V2.0 核心主题**：从"功能原型"到"可部署的生产级平台"

| 目标 | 描述 | 优先级 |
|------|------|--------|
| 前端完整重建 | 基于 Next.js 16 重建全部页面和组件 | P0 |
| 后端架构优化 | 解决连接池、错误处理、代码冗余等问题 | P0 |
| 容器化部署就绪 | 补全 Dockerfile、Nginx 配置 | P0 |
| WebSocket 实时通知 | 新闻更新和分析结果实时推送 | P1 |
| 测试覆盖率 ≥ 70% | 完善单元测试、集成测试 | P1 |
| LLM 智能路由 | 基于负载/成本/质量的模型选择策略 | P1 |
| API 速率限制和安全加固 | 请求限流、CORS 优化、输入验证 | P1 |
| 多租户基础架构 | 数据隔离、租户管理 | P2 |
| 移动端升级 | 升级到 React Native 新架构或 Expo | P2 |

### 4.2 阶段规划

#### 阶段一：基础修复与后端优化（V1.6）

**主题**：修复阻断性问题，优化后端架构

**任务清单**：

1. **依赖版本锁定**
   - 锁定 requirements.txt 所有包版本
   - 创建 requirements-dev.txt（开发依赖）和 requirements-test.txt（测试依赖）

2. **数据库连接池优化**
   - 将 NullPool 替换为 AsyncAdaptedQueuePool
   - 配置连接池参数（pool_size=10, max_overflow=20, pool_timeout=30）

3. **全局异常处理**
   - 添加 FastAPI 全局异常处理中间件
   - 统一 API 错误响应格式 `{"code": int, "message": str, "data": any}`

4. **API 端点合并**
   - 合并 auth_simple.py → auth.py
   - 合并 map_simple.py → map.py
   - 合并 advanced_analysis_simple.py → advanced_analysis.py
   - 合并 i18n_simple.py → i18n.py

5. **测试文件整理**
   - 将根目录 test_*.py 移入 tests/
   - 创建 requirements-test.txt（pytest, pytest-asyncio, httpx 等）
   - 修复 CI 配置引用

6. **Dockerfile 和构建配置**
   - 编写后端 Dockerfile（多阶段构建）
   - 配置 .dockerignore
   - 验证 docker-compose.production.yml 可用性

7. **API 速率限制**
   - 引入 slowapi 中间件
   - 配置不同端点的限流策略

#### 阶段二：前端完整重建（V1.7）

**主题**：基于 Next.js 16 重建全功能 Web 前端

**页面列表**：

| 页面 | 路由 | 功能 |
|------|------|------|
| 首页 | `/` | 新闻列表、筛选、分页 |
| 登录 | `/login` | 用户登录 |
| 注册 | `/register` | 用户注册 |
| 新闻详情 | `/news/[id]` | 新闻详情、AI 分析结果 |
| 全球热点地图 | `/map` | 全球新闻地理分布 |
| 事件时间轴 | `/events` | 事件聚类与脉络 |
| 搜索 | `/search` | 全文搜索 |
| 数据分析 | `/dashboard` | 可视化仪表盘 |
| 高级分析 | `/analysis` | AI 深度分析工具 |
| 报告生成 | `/reports` | 分析报告管理 |
| 个人资料 | `/profile` | 用户资料管理 |
| 设置 | `/settings` | 账户/通知/外观设置 |
| 分析历史 | `/history` | 历史记录管理 |

**技术选型**：
- Next.js 16 (App Router)
- React 19 + TailwindCSS v4
- Shadcn/UI 组件库
- Zustand 状态管理
- Recharts 图表库
- React-Simple-Maps 地图组件
- SWR / React Query 数据获取

**关键特性**：
- 全响应式设计（桌面端 + 移动端）
- 暗色/亮色主题切换
- 骨架屏加载
- 组件懒加载
- SEO 优化（SSR/SSG）
- 中英文国际化

#### 阶段三：实时通信与高级功能（V1.8）

**主题**：WebSocket 实时推送、LLM 智能路由

**任务清单**：

1. **WebSocket 实时通知**
   - 基于 FastAPI WebSocket 实现实时推送
   - 新闻采集完成通知
   - AI 分析结果实时推送
   - 系统告警推送

2. **LLM 智能路由策略**
   - 基于响应时间、成本、质量的加权路由
   - LLM 健康检查和自动熔断
   - 分析结果缓存（相同内容避免重复分析）
   - Token 用量统计和预算控制

3. **高级搜索和过滤**
   - Elasticsearch 集成（可选，PostgreSQL FTS 增强）
   - 多维度组合筛选
   - 保存搜索条件

4. **数据导出增强**
   - 支持 PDF/Excel/JSON/CSV 多格式导出
   - 批量导出和异步处理
   - 导出任务队列

#### 阶段四：生产部署与质量保障（V1.9）

**主题**：测试覆盖、监控告警、部署自动化

**任务清单**：

1. **测试体系完善**
   - 后端单元测试覆盖率 ≥ 80%
   - 前端组件测试覆盖率 ≥ 70%
   - API 集成测试
   - E2E 测试（Playwright）
   - 性能测试（Locust）

2. **监控和可观测性**
   - Prometheus 指标收集
   - Grafana 仪表盘
   - 结构化日志（JSON 格式）
   - APM 追踪（OpenTelemetry）

3. **CI/CD 完善**
   - 修复 GitHub Actions 配置
   - 自动化测试 → 构建 → 部署流程
   - 安全扫描（Trivy + Bandit）
   - Docker 镜像自动构建推送

4. **Nginx 反向代理**
   - 编写 nginx.conf
   - SSL/TLS 配置
   - 静态资源缓存策略
   - WebSocket 代理配置

#### 阶段五：企业级功能（V2.0）

**主题**：多租户、商业化功能

**任务清单**：

1. **多租户架构**
   - 租户数据隔离（schema 或 row-level）
   - 租户管理 API
   - 租户配额和计费

2. **订阅支付系统**
   - 计费方案设计（免费/专业/企业）
   - 支付网关集成
   - 订阅管理

3. **移动端升级**
   - 升级到 React Native 新架构（或 Expo）
   - 推送通知
   - 离线缓存

4. **高可用部署**
   - Kubernetes 部署配置
   - 数据库主从复制
   - Redis Sentinel/Cluster
   - CDN 配置

---

## 五、技术决策和架构改进

### 5.1 数据库优化方案

```
当前: NullPool（无连接池）
改进: AsyncAdaptedQueuePool
  - pool_size: 10
  - max_overflow: 20
  - pool_timeout: 30
  - pool_recycle: 3600
```

### 5.2 API 响应统一格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

### 5.3 LLM 智能路由架构

```
请求 → LLMRouter
         ├── 健康检查: 过滤不可用 provider
         ├── 负载均衡: 选择响应时间最短的 provider
         ├── 成本控制: 优先选择低成本模型
         ├── 质量保障: 关键分析使用高质量模型
         └── 熔断器: 连续失败自动切换
```

### 5.4 前端架构设计

```
app/
├── (auth)/           # 认证相关页面
│   ├── login/
│   └── register/
├── (main)/           # 主要功能页面
│   ├── page.tsx      # 首页（新闻列表）
│   ├── news/[id]/    # 新闻详情
│   ├── map/          # 全球热点地图
│   ├── events/       # 事件时间轴
│   ├── search/       # 搜索
│   ├── dashboard/    # 数据仪表盘
│   ├── analysis/     # 高级分析
│   ├── reports/      # 报告
│   ├── history/      # 分析历史
│   ├── profile/      # 个人资料
│   └── settings/     # 设置
├── components/       # 共享组件
│   ├── ui/           # Shadcn/UI 基础组件
│   ├── layout/       # 布局组件
│   ├── news/         # 新闻相关组件
│   ├── charts/       # 图表组件
│   └── map/          # 地图组件
├── hooks/            # 自定义 Hooks
├── lib/              # 工具函数
├── stores/           # Zustand 状态管理
├── types/            # TypeScript 类型
└── styles/           # 全局样式
```

---

## 六、风险管理

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 前端重建工作量大 | 高 | 高 | 分阶段交付，优先核心页面 |
| LLM API 不稳定 | 中 | 高 | 多 provider 冗余 + 熔断机制 |
| 数据库迁移风险 | 中 | 高 | 完整备份 + 回滚脚本 |
| React Native 过时 | 低 | 中 | 评估 Expo 或 Flutter 替代方案 |
| 多租户数据隔离 | 中 | 高 | 充分测试 + 安全审计 |

---

## 七、成功指标

| 指标 | 当前值 | V2.0 目标 |
|------|--------|-----------|
| 功能完成度 | 60%（前端缺失） | 95%+ |
| 后端测试覆盖率 | ~45% | ≥ 80% |
| 前端测试覆盖率 | 0% | ≥ 70% |
| API 响应时间（P95） | 未测量 | < 200ms |
| 页面首屏加载 | N/A | < 2s |
| 容器化部署 | 不可用 | 一键部署 |
| 安全扫描 | 未执行 | 零高危漏洞 |

---

## 八、附录

### A. 现有 API 端点清单

| 模块 | 端点数 | 状态 |
|------|--------|------|
| News | 4 | ✅ |
| LLM | 3 | ✅ |
| Map | 3 | ✅ |
| Events | 2 | ✅ |
| Auth | 4+ | ✅ |
| Scheduler | 2 | ✅ |
| Preferences | 4 | ✅ |
| Analysis History | 5 | ✅ |
| Reports | 3+ | ✅ |
| Advanced Analysis | 3+ | ✅ |
| i18n | 2 | ✅ |
| **总计** | **~35** | - |

### B. 后端核心模块列表

| 模块 | 文件 | 代码行数 | 说明 |
|------|------|----------|------|
| analyzer.py | app/core/ | 480 | 新闻分析引擎 |
| advanced_nlp.py | app/core/ | 787 | 高级 NLP 分析 |
| llm_client.py | app/core/ | 206 | LLM 统一客户端 |
| report_generator.py | app/core/ | 778 | 报告生成 |
| geo_heatmap.py | app/core/ | 793 | 地理热力图 |
| auth.py | app/core/ | 448 | 认证模块 |
| crawler.py | app/core/ | 90 | RSS 爬虫 |
| worker.py | app/ | 279 | Celery 任务 |
| news.py | app/models/ | 63 | 新闻数据模型 |
| user.py | app/models/ | 268 | 用户数据模型 |

### C. 数据库迁移历史

| 版本 | 文件 | 说明 |
|------|------|------|
| 1 | f56b995b94be | 初始迁移 |
| 2 | 56c2fcd4793d | 添加全文搜索索引 |
| 3 | ff7e7a245174 | 添加 location 字段 |
| 4 | a659dd78ca66 | 添加用户和认证表 |
| 5 | 2f3078d11242 | 添加高级分析字段 |

---

*文档结束*
