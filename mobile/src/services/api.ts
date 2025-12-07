/**
 * API服务
 * 处理与后端API的通信
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  ApiResponse,
  PaginatedResponse,
  User,
  News,
  MapData,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  NewsAnalysis,
  SearchFilters,
  SearchResult,
  HeatmapData,
  ReportRequest,
  Report,
} from '../types';

class ApiService {
  private client: AxiosInstance;
  private baseURL: string;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor() {
    this.baseURL = process.env.API_BASE_URL || 'http://localhost:8001/api/v1';

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器
    this.client.interceptors.request.use(
      async (config) => {
        const token = await this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (!this.isRefreshing) {
            this.isRefreshing = true;
            try {
              const newToken = await this.refreshToken();
              this.isRefreshing = false;
              this.refreshSubscribers.forEach(callback => callback(newToken));
              this.refreshSubscribers = [];
              return this.client(originalRequest);
            } catch (refreshError) {
              this.isRefreshing = false;
              await this.logout();
              throw refreshError;
            }
          } else {
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(this.client(originalRequest));
              });
            });
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async getAccessToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('@auth_access_token');
    } catch (error) {
      console.error('Failed to get access token:', error);
      return null;
    }
  }

  private async getRefreshToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('@auth_refresh_token');
    } catch (error) {
      console.error('Failed to get refresh token:', error);
      return null;
    }
  }

  private async setTokens(accessToken: string, refreshToken: string): Promise<void> {
    try {
      await AsyncStorage.multiSet([
        ['@auth_access_token', accessToken],
        ['@auth_refresh_token', refreshToken],
      ]);
    } catch (error) {
      console.error('Failed to set tokens:', error);
      throw error;
    }
  }

  private async refreshToken(): Promise<string> {
    try {
      const refreshToken = await this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(
        `${this.baseURL}/auth/refresh`,
        {},
        {
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        }
      );

      const { access_token, refresh_token: newRefreshToken } = response.data;
      await this.setTokens(access_token, newRefreshToken);

      return access_token;
    } catch (error) {
      console.error('Failed to refresh token:', error);
      throw error;
    }
  }

  private async logout(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        '@auth_access_token',
        '@auth_refresh_token',
        '@user_data',
      ]);
    } catch (error) {
      console.error('Failed to logout:', error);
    }
  }

  // 认证相关API
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await this.client.post<ApiResponse<LoginResponse>>('/auth/login', credentials);
      const { access_token, refresh_token, user } = response.data.data!;

      await this.setTokens(access_token, refresh_token);
      await AsyncStorage.setItem('@user_data', JSON.stringify(user));

      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async register(userData: RegisterRequest): Promise<User> {
    try {
      const response = await this.client.post<ApiResponse<User>>('/auth/register', userData);
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await this.client.get<ApiResponse<User>>('/auth/me');
      return response.data.data!;
    } catch (error) {
      console.error('Failed to get current user:', error);
      return null;
    }
  }

  async logoutApi(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch (error) {
      console.error('API logout failed:', error);
    } finally {
      await this.logout();
    }
  }

  // 新闻相关API
  async getNews(
    page: number = 1,
    size: number = 20,
    filters?: SearchFilters
  ): Promise<PaginatedResponse<News>> {
    try {
      const params = { page, size, ...filters };
      const response = await this.client.get<ApiResponse<PaginatedResponse<News>>>('/news', { params });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async getNewsDetail(id: number): Promise<News> {
    try {
      const response = await this.client.get<ApiResponse<News>>(`/news/${id}`);
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async analyzeNews(newsId: number): Promise<NewsAnalysis> {
    try {
      const response = await this.client.post<ApiResponse<NewsAnalysis>>(`/advanced-analysis/analyze`, {
        news_id: newsId,
        title: '',
        content: '',
        enable_sentiment_prediction: true,
        enable_entity_extraction: true,
        enable_relation_extraction: true,
      });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async searchNews(
    query: string,
    page: number = 1,
    size: number = 20,
    filters?: SearchFilters
  ): Promise<SearchResult> {
    try {
      const params = { q: query, page, size, ...filters };
      const response = await this.client.get<ApiResponse<SearchResult>>('/news/search', { params });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  // 地图相关API
  async getMapData(
    limit: number = 100,
    category?: string,
    minSentiment?: number,
    maxSentiment?: number
  ): Promise<MapData> {
    try {
      const params = { limit, category, min_sentiment: minSentiment, max_sentiment: maxSentiment };
      const response = await this.client.get<ApiResponse<MapData>>('/map/news-locations', { params });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async getHeatmapData(
    bbox?: number[],
    timeRange: string = 'day',
    gridType: string = 'global',
    sentimentFilter?: number[]
  ): Promise<HeatmapData> {
    try {
      const params = {
        time_range: timeRange,
        grid_type: gridType,
        sentiment_filter: sentimentFilter,
      };

      if (bbox) {
        params['bbox'] = bbox;
      }

      const response = await this.client.post<ApiResponse<HeatmapData>>(
        '/map/heatmap/advanced',
        { bbox, time_range: timeRange, grid_type: gridType, sentiment_filter: sentimentFilter }
      );
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async getHotspots(
    limit: number = 20,
    minIntensity: number = 0.1,
    timeRange: string = 'day'
  ): Promise<any> {
    try {
      const params = { limit, min_intensity: minIntensity, time_range: timeRange };
      const response = await this.client.get<ApiResponse<any>>('/map/hotspots', { params });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  // 分析相关API
  async getSentimentAnalysis(text: string): Promise<any> {
    try {
      const response = await this.client.post<ApiResponse<any>>('/advanced-analysis/sentiment', {
        title: text.substring(0, 100),
        content: text,
        use_multi_model: true,
      });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async extractEntities(text: string): Promise<any> {
    try {
      const response = await this.client.post<ApiResponse<any>>('/advanced-analysis/entities', {
        title: text.substring(0, 100),
        content: text,
        include_relations: true,
      });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  // 报告相关API
  async generateReport(request: ReportRequest): Promise<Report> {
    try {
      const response = await this.client.post<ApiResponse<Report>>('/reports/generate/news-analysis', request);
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async getReports(limit: number = 50): Promise<Report[]> {
    try {
      const response = await this.client.get<ApiResponse<Report[]>>('/reports/list', { params: { limit } });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async downloadReport(filename: string): Promise<string> {
    try {
      const response = await this.client.get(`/reports/download/${filename}`, {
        responseType: 'blob',
      });

      // 在移动端，这里需要处理文件的保存逻辑
      // 可以使用 react-native-fs 或类似库来保存文件
      return response.data as any;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  // 国际化相关API
  async getTranslations(language: string, domain?: string): Promise<any> {
    try {
      const params = { domain };
      const response = await this.client.get<ApiResponse<any>>(`/i18n/translations/${language}`, { params });
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async translateText(key: string, language?: string, domain?: string): Promise<string> {
    try {
      const params = { key, language, domain };
      const response = await this.client.get<ApiResponse<{ translated_text: string }>>('/i18n/translate', { params });
      return response.data.data!.translated_text;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  private handleError(error: any) {
    if (error.response) {
      // 服务器响应错误
      const { status, data } = error.response;
      console.error(`API Error ${status}:`, data);
    } else if (error.request) {
      // 网络错误
      console.error('Network Error:', error.message);
    } else {
      // 其他错误
      console.error('Error:', error.message);
    }
  }

  // 工具方法
  async getApiStatus(): Promise<any> {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('API status check failed:', error);
      return { status: 'error', message: error.message };
    }
  }

  async getReportGenerationStatus(): Promise<any> {
    try {
      const response = await this.client.get<ApiResponse<any>>('/reports/status');
      return response.data.data!;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }
}

// 创建单例实例
export const apiService = new ApiService();
export default apiService;