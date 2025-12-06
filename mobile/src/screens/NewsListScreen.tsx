/**
 * 新闻列表屏幕
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TextInput,
  TouchableOpacity,
  Modal,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types';
import NewsCard from '../components/NewsCard';
import { apiService } from '../services/api';
import { News, SearchFilters } from '../types';

type NewsListScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Main'>;

interface Props {
  navigation: NewsListScreenNavigationProp;
}

const NewsListScreen: React.FC<Props> = ({ navigation }) => {
  const [news, setNews] = useState<News[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchVisible, setSearchVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    loadNews();
  }, []);

  const loadNews = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setPage(1);
        setHasMore(true);
      }

      const currentPage = isRefresh ? 1 : page;
      const response = await apiService.getNews(
        currentPage,
        20,
        Object.keys(filters).length > 0 ? filters : undefined
      );

      if (isRefresh) {
        setNews(response.data);
      } else {
        setNews(prev => [...prev, ...response.data]);
      }

      setHasMore(response.pagination.page < response.pagination.pages);
      setPage(currentPage + 1);
    } catch (error) {
      console.error('Failed to load news:', error);
      Alert.alert('错误', '加载新闻失败，请重试');
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [page, filters]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadNews(true);
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasMore && !refreshing) {
      setLoadingMore(true);
      loadNews();
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchVisible(false);
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.searchNews(searchQuery, 1, 20, filters);
      setNews(response.data);
      setSearchVisible(false);
      setSearchQuery('');
    } catch (error) {
      console.error('Search failed:', error);
      Alert.alert('错误', '搜索失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleNewsPress = (newsItem: News) => {
    navigation.navigate('NewsDetail', { newsId: newsItem.id });
  };

  const openFilters = () => {
    navigation.navigate('Search', { query: searchQuery });
  };

  const renderNewsItem = ({ item }: { item: News }) => (
    <NewsCard
      news={item}
      onPress={handleNewsPress}
      showImage={true}
      showSentiment={true}
      compact={false}
    />
  );

  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.footerText}>加载更多...</Text>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>加载新闻中...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* 头部 */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>SmartInsight</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setSearchVisible(true)}
          >
            <Icon name="search" size={24} color="#333" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={openFilters}
          >
            <Icon name="filter-list" size={24} color="#333" />
          </TouchableOpacity>
        </View>
      </View>

      {/* 新闻列表 */}
      <FlatList
        data={news}
        renderItem={renderNewsItem}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.1}
        ListFooterComponent={renderFooter}
        contentContainerStyle={styles.newsList}
        showsVerticalScrollIndicator={false}
      />

      {/* 搜索模态框 */}
      <Modal
        visible={searchVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSearchVisible(false)}
      >
        <SafeAreaView style={styles.searchModal}>
          <View style={styles.searchHeader}>
            <TouchableOpacity
              style={styles.searchBackButton}
              onPress={() => setSearchVisible(false)}
            >
              <Icon name="arrow-back" size={24} color="#333" />
            </TouchableOpacity>
            <TextInput
              style={styles.searchInput}
              placeholder="搜索新闻..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              autoFocus
              onSubmitEditing={handleSearch}
              returnKeyType="search"
            />
            <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
              <Icon name="search" size={24} color="#007AFF" />
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  headerActions: {
    flexDirection: 'row',
  },
  actionButton: {
    padding: 8,
    marginLeft: 8,
  },
  newsList: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  footerLoader: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
  },
  footerText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  searchModal: {
    flex: 1,
    backgroundColor: '#FFF',
  },
  searchHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  searchBackButton: {
    padding: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginHorizontal: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    backgroundColor: '#F8F8F8',
  },
  searchButton: {
    padding: 8,
  },
});

export default NewsListScreen;