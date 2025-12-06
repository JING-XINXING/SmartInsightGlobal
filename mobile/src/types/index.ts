/**
 * TypeScript类型定义
 */

// 用户相关类型
export interface User {
  id: number;
  email: string;
  username: string;
  role: 'admin' | 'analyst' | 'viewer' | 'guest';
  permissions: string[];
  is_active: boolean;
  created_at: string;
  last_login?: string;
  avatar_url?: string;
}

// 新闻相关类型
export interface News {
  id: number;
  title: string;
  content: string;
  summary?: string;
  source: string;
  url: string;
  publish_date: string;
  created_at: string;
  sentiment_score?: number;
  sentiment_confidence?: number;
  keywords?: string[];
  category?: string;
  location?: {
    country?: string;
    country_cn?: string;
    city?: string;
    lat?: number;
    lng?: number;
  };
  entities?: Entity[];
  emotions?: EmotionScores;
  language?: string;
  analysis_quality?: number;
}

export interface Entity {
  text: string;
  type: 'person' | 'organization' | 'location' | 'event' | 'product' | 'date' | 'money' | 'percent' | 'other';
  confidence: number;
  metadata?: Record<string, any>;
}

export interface EmotionScores {
  joy: number;
  sadness: number;
  anger: number;
  fear: number;
  surprise: number;
  disgust: number;
  neutral: number;
}

// 地图相关类型
export interface MapData {
  locations: NewsLocation[];
  clusters: LocationCluster[];
  total_with_location: number;
  total_news: number;
}

export interface NewsLocation {
  id: number;
  title: string;
  source: string;
  publish_date: string;
  sentiment_score?: number;
  category?: string;
  country?: string;
  country_cn?: string;
  city?: string;
  lat?: number;
  lng?: number;
}

export interface LocationCluster {
  country: string;
  country_cn: string;
  lat: number;
  lng: number;
  count: number;
  avg_sentiment: number;
  news_ids: number[];
}

export interface HotspotRegion {
  center_lat: number;
  center_lng: number;
  radius: number;
  intensity: number;
  news_count: number;
  avg_sentiment: number;
  dominant_category: string;
  trend: 'increasing' | 'decreasing' | 'stable';
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T = any> {
  success: boolean;
  data: T[];
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
  };
}

// 认证相关类型
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  first_name?: string;
  last_name?: string;
}

// 分析结果类型
export interface SentimentAnalysis {
  sentiment_score: number;
  confidence: number;
  emotion_scores: EmotionScores;
  trend?: 'increasing' | 'decreasing' | 'stable';
  key_factors?: string[];
}

export interface NewsAnalysis {
  sentiment: SentimentAnalysis;
  entities: Entity[];
  relations: Relation[];
  keywords: string[];
  category: string;
  prediction?: {
    trend: string;
    confidence: number;
    horizon: string;
    factors: string[];
  };
}

export interface Relation {
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
}

// 报告相关类型
export interface ReportRequest {
  title: string;
  report_type: 'news_analysis' | 'sentiment_trend' | 'geographic_analysis' | 'comprehensive_report' | 'custom';
  format: 'pdf' | 'html' | 'markdown';
  language?: string;
  time_range?: string;
  filters?: Record<string, any>;
  include_charts?: boolean;
  include_raw_data?: boolean;
}

export interface Report {
  id: string;
  title: string;
  format: string;
  filename: string;
  file_size: number;
  created_at: string;
  status: 'generating' | 'completed' | 'failed';
  download_url?: string;
}

// 应用配置类型
export interface AppConfig {
  api_base_url: string;
  map_api_key?: string;
  enable_notifications: boolean;
  enable_location_tracking: boolean;
  auto_refresh_interval: number;
  cache_duration: number;
  theme: 'light' | 'dark' | 'auto';
  language: string;
}

// 通知类型
export interface NotificationData {
  id: string;
  title: string;
  body: string;
  type: 'news_update' | 'sentiment_alert' | 'system' | 'report_ready';
  data?: Record<string, any>;
  created_at: string;
  read: boolean;
}

// 搜索相关类型
export interface SearchFilters {
  category?: string[];
  sentiment_range?: [number, number];
  date_range?: [string, string];
  location?: string;
  keywords?: string[];
  source?: string[];
}

export interface SearchResult {
  news: News[];
  total: number;
  page: number;
  size: number;
  facets: {
    categories: Record<string, number>;
    sentiments: Record<string, number>;
    sources: Record<string, number>;
  };
}

// 热力图类型
export interface HeatmapData {
  metadata: {
    generated_at: string;
    processing_time: number;
    time_range: string;
    grid_type: string;
    total_news: number;
    bbox?: number[];
  };
  grid_cells: Array<{
    bounds: number[];
    center: number[];
    intensity: number;
    news_count: number;
    avg_sentiment: number;
    categories: Record<string, number>;
  }>;
  hotspots: Array<{
    center: number[];
    radius: number;
    intensity: number;
    news_count: number;
    avg_sentiment: number;
    dominant_category: string;
    trend: string;
  }>;
  time_series: Array<{
    timestamp: string;
    location_count: number;
    avg_intensity: number;
    avg_sentiment: number;
    top_categories: Array<{ category: string; count: number }>;
    total_news: number;
  }>;
  statistics: {
    total_news: number;
    news_with_location: number;
    location_coverage_rate: number;
    avg_sentiment: number;
    category_distribution: Record<string, number>;
    grid_statistics: {
      total_cells: number;
      active_cells: number;
      max_intensity: number;
      avg_cell_intensity: number;
    };
    geographic_coverage: {
      lat_range: number[];
      lng_range: number[];
      center_lat: number;
      center_lng: number;
    };
  };
}

// 本地存储类型
export interface StorageKeys {
  ACCESS_TOKEN: '@auth_access_token';
  REFRESH_TOKEN: '@auth_refresh_token';
  USER_DATA: '@user_data';
  APP_CONFIG: '@app_config';
  SEARCH_HISTORY: '@search_history';
  FAVORITE_NEWS: '@favorite_news';
  NOTIFICATION_SETTINGS: '@notification_settings';
  THEME: '@theme';
  LANGUAGE: '@language';
}

// 导航相关类型
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  NewsDetail: { newsId: number };
  MapView: undefined;
  Analysis: undefined;
  Reports: undefined;
  Settings: undefined;
  Profile: undefined;
  Search: { query?: string };
  HotspotDetail: { hotspot: HotspotRegion };
  ReportViewer: { reportId: string };
};

export type MainTabParamList = {
  News: undefined;
  Map: undefined;
  Analysis: undefined;
  Reports: undefined;
  Profile: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

// 组件Props类型
export interface NewsCardProps {
  news: News;
  onPress?: (news: News) => void;
  showImage?: boolean;
  showSentiment?: boolean;
  compact?: boolean;
}

export interface MapMarkerProps {
  news: News;
  onPress?: (news: News) => void;
}

export interface SentimentIndicatorProps {
  score: number;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

export interface ChartProps {
  data: any[];
  type: 'line' | 'bar' | 'pie' | 'scatter';
  title?: string;
  height?: number;
  width?: number;
}

// 错误类型
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// 网络状态类型
export interface NetworkState {
  isConnected: boolean;
  type: string;
  isInternetReachable: boolean;
  details?: any;
}