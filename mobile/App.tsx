/**
 * SmartInsight Global 移动应用主入口
 */

import React, { useEffect, useState } from 'react';
import { StatusBar, LogBox } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';

// 导入屏幕
import AuthScreen from './src/screens/AuthScreen';
import NewsListScreen from './src/screens/NewsListScreen';
import MapScreen from './src/screens/MapScreen';
import AnalysisScreen from './src/screens/AnalysisScreen';
import ReportsScreen from './src/screens/ReportsScreen';
import ProfileScreen from './src/screens/ProfileScreen';

// 导入服务
import { apiService } from './src/services/api';
import { User } from './src/types';

// 忽略特定警告
LogBox.ignoreLogs(['VirtualizedLists should never be nested']);

// 导航类型
type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  NewsDetail: { newsId: number };
  Settings: undefined;
};

type MainTabParamList = {
  News: undefined;
  Map: undefined;
  Analysis: undefined;
  Reports: undefined;
  Profile: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

const MainTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'News':
              iconName = 'article';
              break;
            case 'Map':
              iconName = 'map';
              break;
            case 'Analysis':
              iconName = 'analytics';
              break;
            case 'Reports':
              iconName = 'description';
              break;
            case 'Profile':
              iconName = 'person';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#666',
        tabBarStyle: {
          backgroundColor: '#FFF',
          borderTopWidth: 1,
          borderTopColor: '#E0E0E0',
          paddingBottom: 5,
          height: 60,
        },
        tabBarLabelStyle: {
          fontSize: 12,
        },
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="News"
        component={NewsListScreen}
        options={{
          tabBarLabel: '新闻',
        }}
      />
      <Tab.Screen
        name="Map"
        component={MapScreen}
        options={{
          tabBarLabel: '地图',
        }}
      />
      <Tab.Screen
        name="Analysis"
        component={AnalysisScreen}
        options={{
          tabBarLabel: '分析',
        }}
      />
      <Tab.Screen
        name="Reports"
        component={ReportsScreen}
        options={{
          tabBarLabel: '报告',
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarLabel: '我的',
        }}
      />
    </Tab.Navigator>
  );
};

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    checkAuthenticationStatus();
  }, []);

  const checkAuthenticationStatus = async () => {
    try {
      const currentUser = await apiService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Authentication check failed:', error);
      setIsAuthenticated(false);
    }
  };

  const handleLogin = (userData: User) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    try {
      await apiService.logoutApi();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout failed:', error);
      // 即使API调用失败，也要清除本地状态
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  // 显示加载状态
  if (isAuthenticated === null) {
    return (
      <StatusBar
        barStyle="dark-content"
        backgroundColor="#F5F5F5"
        translucent={false}
      />
    );
  }

  return (
    <NavigationContainer>
      <StatusBar
        barStyle="dark-content"
        backgroundColor="#FFF"
        translucent={false}
      />

      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated && user ? (
          <>
            <Stack.Screen name="Main">
              {() => (
                <MainTabNavigator />
              )}
            </Stack.Screen>
            <Stack.Screen
              name="NewsDetail"
              getComponent={() => require('./src/screens/NewsDetailScreen').default}
              options={{
                presentation: 'modal',
                headerShown: true,
                title: '新闻详情',
              }}
            />
            <Stack.Screen
              name="Settings"
              getComponent={() => require('./src/screens/SettingsScreen').default}
              options={{
                headerShown: true,
                title: '设置',
              }}
            />
          </>
        ) : (
          <Stack.Screen name="Auth">
            {() => (
              <AuthScreen onLogin={handleLogin} />
            )}
          </Stack.Screen>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;