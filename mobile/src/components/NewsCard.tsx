/**
 * 新闻卡片组件
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import { Card, Button, Chip } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import FastImage from 'react-native-fast-image';
import { News } from '../types';
import SentimentIndicator from './SentimentIndicator';
import { getLocalizedCategory, formatDate, formatTimeAgo } from '../utils/helpers';

interface NewsCardProps {
  news: News;
  onPress?: (news: News) => void;
  showImage?: boolean;
  showSentiment?: boolean;
  compact?: boolean;
  language?: string;
}

const NewsCard: React.FC<NewsCardProps> = ({
  news,
  onPress,
  showImage = true,
  showSentiment = true,
  compact = false,
  language = 'zh-CN',
}) => {
  const screenWidth = Dimensions.get('window').width;

  const handlePress = () => {
    onPress?.(news);
  };

  const getSentimentColor = (score?: number) => {
    if (!score) return '#666';
    if (score > 30) return '#4CAF50';
    if (score < -30) return '#F44336';
    return '#FF9800';
  };

  const getCategoryColor = (category?: string) => {
    const colors: { [key: string]: string } = {
      '政治': '#2196F3',
      '经济': '#4CAF50',
      '军事': '#F44336',
      '科技': '#9C27B0',
      '社会': '#FF9800',
      '文化': '#795548',
      '体育': '#00BCD4',
      '健康': '#8BC34A',
      '环境': '#4CAF50',
      '灾难': '#F44336',
      '国际关系': '#3F51B5',
      'other': '#9E9E9E',
    };
    return colors[category || 'other'] || '#9E9E9E';
  };

  return (
    <Card containerStyle={styles.card}>
      <TouchableOpacity onPress={handlePress} activeOpacity={0.7}>
        <View style={styles.container}>
          {/* 头部信息 */}
          <View style={styles.header}>
            <Text style={styles.source}>{news.source}</Text>
            <Text style={styles.time}>
              {formatTimeAgo(news.publish_date, language)}
            </Text>
          </View>

          {/* 标题 */}
          <Text style={compact ? styles.titleCompact : styles.title} numberOfLines={compact ? 2 : 3}>
            {news.title}
          </Text>

          {/* 图片 */}
          {showImage && !compact && news.summary && (
            <FastImage
              style={[styles.image, { width: screenWidth - 32 }]}
              source={{
                uri: `https://picsum.photos/seed/${news.id}/400/200`,
                priority: FastImage.priority.normal,
              }}
              resizeMode={FastImage.resizeMode.cover}
            />
          )}

          {/* 摘要 */}
          {!compact && news.summary && (
            <Text style={styles.summary} numberOfLines={3}>
              {news.summary}
            </Text>
          )}

          {/* 标签和情感指示器 */}
          <View style={styles.footer}>
            <View style={styles.leftSection}>
              {/* 类别标签 */}
              {news.category && (
                <Chip
                  title={getLocalizedCategory(news.category, language)}
                  type="outline"
                  buttonStyle={{
                    borderColor: getCategoryColor(news.category),
                    backgroundColor: `${getCategoryColor(news.category)}10`,
                  }}
                  titleStyle={{
                    color: getCategoryColor(news.category),
                    fontSize: 12,
                  }}
                  containerStyle={styles.chip}
                />
              )}

              {/* 关键词 */}
              {news.keywords && news.keywords.length > 0 && (
                <View style={styles.keywordsContainer}>
                  {news.keywords.slice(0, 2).map((keyword, index) => (
                    <Chip
                      key={index}
                      title={keyword}
                      type="outline"
                      buttonStyle={{
                        borderColor: '#E0E0E0',
                        backgroundColor: '#F5F5F5',
                      }}
                      titleStyle={{
                        color: '#666',
                        fontSize: 11,
                      }}
                      containerStyle={styles.keywordChip}
                    />
                  ))}
                </View>
              )}
            </View>

            {/* 情感指示器 */}
            {showSentiment && news.sentiment_score !== undefined && (
              <SentimentIndicator
                score={news.sentiment_score}
                size="small"
                showLabel={false}
              />
            )}
          </View>

          {/* 底部信息 */}
          <View style={styles.bottomInfo}>
            <View style={styles.infoItem}>
              <Icon name="visibility" size={16} color="#666" />
              <Text style={styles.infoText}>阅读</Text>
            </View>
            {news.location && news.location.country && (
              <View style={styles.infoItem}>
                <Icon name="location-on" size={16} color="#666" />
                <Text style={styles.infoText}>
                  {language === 'zh-CN' ? news.location.country_cn : news.location.country}
                </Text>
              </View>
            )}
            {news.analysis_quality && (
              <View style={styles.infoItem}>
                <Icon name="analytics" size={16} color="#666" />
                <Text style={styles.infoText}>
                  质量: {Math.round(news.analysis_quality * 100)}%
                </Text>
              </View>
            )}
          </View>

          {/* 实体指示器 */}
          {news.entities && news.entities.length > 0 && (
            <View style={styles.entitiesContainer}>
              <Icon name="people" size={14} color="#666" />
              <Text style={styles.entitiesText}>
                {news.entities.length} 个实体
              </Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 8,
    marginVertical: 4,
    borderRadius: 12,
    elevation: 2,
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  container: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  source: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  time: {
    fontSize: 11,
    color: '#999',
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    lineHeight: 22,
    marginBottom: 8,
  },
  titleCompact: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    lineHeight: 20,
    marginBottom: 6,
  },
  summary: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  image: {
    height: 200,
    borderRadius: 8,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  leftSection: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  chip: {
    marginRight: 6,
    marginBottom: 4,
  },
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  keywordChip: {
    marginRight: 4,
    marginBottom: 4,
  },
  bottomInfo: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoText: {
    fontSize: 11,
    color: '#666',
    marginLeft: 4,
  },
  entitiesContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  entitiesText: {
    fontSize: 11,
    color: '#666',
    marginLeft: 4,
  },
});

export default NewsCard;