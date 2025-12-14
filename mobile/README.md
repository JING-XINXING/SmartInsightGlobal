# SmartInsight Global Mobile App

SmartInsight Global 的 React Native 移动应用，提供全球新闻分析、情感分析、地理热力图等功能。

## 功能特性

### 📱 核心功能
- **新闻浏览**: 查看全球新闻，支持分类筛选和情感分析
- **情感分析**: 实时新闻情感分析和预测
- **地理热力图**: 全球新闻热点可视化
- **高级分析**: NLP实体识别、关系抽取、趋势预测
- **报告生成**: 支持PDF、HTML、Markdown格式报告
- **多语言支持**: 中文和英文界面
- **离线缓存**: 支持离线阅读和缓存

### 🔐 安全特性
- JWT身份认证
- 基于角色的访问控制(RBAC)
- 安全的API通信
- 本地数据加密存储

### 🎨 用户界面
- Material Design风格
- 响应式设计
- 暗黑模式支持
- 流畅的动画效果

## 技术栈

### 前端框架
- **React Native 0.72.4**: 跨平台移动应用框架
- **TypeScript**: 类型安全的JavaScript
- **React Navigation 6**: 导航和路由管理

### UI组件库
- **React Native Elements**: UI组件库
- **React Native Vector Icons**: 图标库
- **React Native Paper**: Material Design组件
- **React Native Reanimated**: 高性能动画库

### 状态管理
- **AsyncStorage**: 本地数据存储
- **React Native Keychain**: 安全存储敏感信息

### 地图和图表
- **React Native Maps**: 地图组件
- **React Native Chart Kit**: 图表库
- **React Native SVG**: SVG图形支持

### 网络和数据处理
- **Axios**: HTTP客户端
- **React Native Fast Image**: 高性能图片加载
- **React Native NetInfo**: 网络状态检测

### 国际化
- **React Native Localization**: 多语言支持
- **React Native Localize**: 本地化设置

## 项目结构

```
mobile/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── NewsCard.tsx
│   │   ├── SentimentIndicator.tsx
│   │   └── ...
│   ├── screens/            # 页面组件
│   │   ├── AuthScreen.tsx
│   │   ├── NewsListScreen.tsx
│   │   ├── MapScreen.tsx
│   │   ├── AnalysisScreen.tsx
│   │   ├── ReportsScreen.tsx
│   │   └── ProfileScreen.tsx
│   ├── services/           # 服务层
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── storage.ts
│   ├── navigation/         # 导航配置
│   │   ├── AppNavigator.tsx
│   │   └── AuthNavigator.tsx
│   ├── utils/              # 工具函数
│   │   ├── helpers.ts
│   │   ├── constants.ts
│   │   └── formatters.ts
│   ├── types/              # TypeScript类型定义
│   │   └── index.ts
│   ├── constants/          # 常量配置
│   │   ├── colors.ts
│   │   ├── sizes.ts
│   │   └── api.ts
│   └── assets/             # 静态资源
│       ├── images/
│       ├── fonts/
│       └── icons/
├── android/                # Android原生代码
├── ios/                    # iOS原生代码
├── App.tsx                 # 应用入口
├── index.js                # 注册文件
├── package.json            # 依赖配置
└── README.md               # 项目说明
```

## 安装和运行

### 环境要求
- Node.js >= 16
- React Native CLI
- Android Studio (Android开发)
- Xcode (iOS开发)

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/JING-XINXING/SmartInsightGlobal.git
cd SmartInsightGlobal/mobile

# 安装依赖
npm install

# iOS依赖 (仅macOS)
cd ios && pod install && cd ..
```

### 运行应用

```bash
# 启动Metro服务器
npm start

# 运行Android版本
npm run android

# 运行iOS版本
npm run ios
```

### 构建发布版本

```bash
# Android发布版本
npm run build:android

# iOS发布版本
npm run build:ios
```

## 配置

### 环境变量
在项目根目录创建 `.env` 文件：

```env
API_BASE_URL=http://your-api-server.com/api/v1
MAP_API_KEY=your-map-api-key
ENABLE_ANALYTICS=true
```

### API配置
更新 `src/services/api.ts` 中的API基础URL：

```typescript
private baseURL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
```

## 开发指南

### 组件开发
- 使用TypeScript编写组件
- 遵循React Hook最佳实践
- 使用PropTypes或TypeScript接口定义props
- 保持组件的单一职责

### 样式规范
- 使用StyleSheet创建样式
- 遵循响应式设计原则
- 使用设计系统的一致颜色和尺寸
- 支持暗黑模式

### 状态管理
- 使用React Hooks管理本地状态
- 使用AsyncStorage持久化数据
- 使用Context API共享全局状态
- 避免不必要的重新渲染

### 错误处理
- 实现全局错误边界
- 提供友好的错误提示
- 记录错误日志
- 实现重试机制

## 测试

```bash
# 运行单元测试
npm test

# 运行lint检查
npm run lint

# 生成测试覆盖率报告
npm run test:coverage
```

## 性能优化

### 图片优化
- 使用React Native Fast Image
- 实现图片懒加载
- 压缩和缓存图片

### 列表优化
- 使用FlatList而非ScrollView
- 实现虚拟化列表
- 优化渲染性能

### 网络优化
- 实现请求缓存
- 使用分页加载
- 优化API调用

### 内存管理
- 及时清理事件监听器
- 避免内存泄漏
- 优化大对象存储

## 部署

### Android部署
1. 生成签名密钥
2. 配置build.gradle
3. 构建APK或AAB
4. 上传到Google Play

### iOS部署
1. 配置Xcode项目
2. 生成证书和描述文件
3. 构建IPA文件
4. 上传到App Store

## 版本发布

### 版本号管理
- 使用语义化版本控制
- 更新package.json版本号
- 生成changelog

### 发布流程
1. 代码审查
2. 运行测试
3. 构建发布版本
4. 内测验证
5. 正式发布

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request
5. 代码审查
6. 合并到主分支

## 许可证

本项目采用 MIT 许可证。

## 支持

- 📧 邮箱: support@smartinsight.global
- 📱 问题反馈: GitHub Issues
- 📖 文档: [项目文档](https://docs.smartinsight.global)

## 更新日志

### v1.0.0 (2025-12-03)
- 初始版本发布
- 基础新闻浏览功能
- 情感分析功能
- 地理热力图
- 用户认证系统
- 报告生成功能
- 多语言支持