/**
 * 情感指示器组件
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface SentimentIndicatorProps {
  score: number;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  language?: string;
}

const SentimentIndicator: React.FC<SentimentIndicatorProps> = ({
  score,
  size = 'medium',
  showLabel = true,
  language = 'zh-CN',
}) => {
  const getSentimentInfo = (score: number) => {
    if (score > 50) {
      return {
        color: '#4CAF50',
        icon: 'sentiment-very-satisfied',
        label: language === 'zh-CN' ? '非常积极' : 'Very Positive',
      };
    } else if (score > 20) {
      return {
        color: '#8BC34A',
        icon: 'sentiment-satisfied',
        label: language === 'zh-CN' ? '积极' : 'Positive',
      };
    } else if (score > -20) {
      return {
        color: '#FFC107',
        icon: 'sentiment-neutral',
        label: language === 'zh-CN' ? '中性' : 'Neutral',
      };
    } else if (score > -50) {
      return {
        color: '#FF9800',
        icon: 'sentiment-dissatisfied',
        label: language === 'zh-CN' ? '消极' : 'Negative',
      };
    } else {
      return {
        color: '#F44336',
        icon: 'sentiment-very-dissatisfied',
        label: language === 'zh-CN' ? '非常消极' : 'Very Negative',
      };
    }
  };

  const getSizeConfig = (size: string) => {
    switch (size) {
      case 'small':
        return {
          iconSize: 16,
          fontSize: 10,
          circleSize: 20,
        };
      case 'large':
        return {
          iconSize: 24,
          fontSize: 14,
          circleSize: 32,
        };
      default:
        return {
          iconSize: 20,
          fontSize: 12,
          circleSize: 26,
        };
    }
  };

  const sentimentInfo = getSentimentInfo(score);
  const sizeConfig = getSizeConfig(size);

  return (
    <View style={styles.container}>
      <View style={[styles.circle, { backgroundColor: sentimentInfo.color }]}>
        <Icon
          name={sentimentInfo.icon}
          size={sizeConfig.iconSize}
          color="white"
        />
      </View>
      {showLabel && (
        <Text
          style={[
            styles.label,
            {
              color: sentimentInfo.color,
              fontSize: sizeConfig.fontSize,
            },
          ]}
        >
          {score}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  circle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    justifyContent: 'center',
    alignItems: 'center',
  },
  label: {
    marginLeft: 6,
    fontWeight: 'bold',
  },
});

export default SentimentIndicator;