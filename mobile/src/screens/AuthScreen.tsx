import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    ActivityIndicator,
    Alert,
    KeyboardAvoidingView,
    Platform,
    ScrollView,
} from 'react-native';
import { apiService } from '../services/api';
import { User } from '../types';

interface AuthScreenProps {
    onLogin: (user: User) => void;
}

const AuthScreen: React.FC<AuthScreenProps> = ({ onLogin }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    // Register fields
    const [username, setUsername] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        if (!email || !password) {
            Alert.alert('Error', 'Please fill in all fields');
            return;
        }

        setLoading(true);
        try {
            if (isLogin) {
                // Login
                const response = await apiService.login({ email, password });
                // The apiService.login returns LoginResponse, but checking api.ts it returns response.data.data! which is LoginResponse
                // LoginResponse contains { access_token, user, ... }
                // Wait, api.ts Line 169 destructures: const { access_token, refresh_token, user } = response.data.data!;
                // And returns response.data.data!
                onLogin(response.user);
            } else {
                // Register
                if (password !== confirmPassword) {
                    Alert.alert('Error', 'Passwords do not match');
                    setLoading(false);
                    return;
                }
                if (!username) {
                    Alert.alert('Error', 'Username is required');
                    setLoading(false);
                    return;
                }

                const user = await apiService.register({
                    email,
                    password,
                    username,
                    confirm_password: confirmPassword,
                });

                // Auto login after register? Or just switch to login?
                Alert.alert('Success', 'Registration successful. Please login.');
                setIsLogin(true);
            }
        } catch (error: any) {
            console.error('Auth error:', error);
            Alert.alert('Authentication Failed', error.response?.data?.message || error.message || 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.container}
        >
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <View style={styles.header}>
                    <Text style={styles.title}>SmartInsight Global</Text>
                    <Text style={styles.subtitle}>{isLogin ? 'Welcome Back' : 'Create Account'}</Text>
                </View>

                <View style={styles.form}>
                    {!isLogin && (
                        <View style={styles.inputContainer}>
                            <Text style={styles.label}>Username</Text>
                            <TextInput
                                style={styles.input}
                                value={username}
                                onChangeText={setUsername}
                                placeholder="Enter your username"
                                autoCapitalize="none"
                            />
                        </View>
                    )}

                    <View style={styles.inputContainer}>
                        <Text style={styles.label}>Email</Text>
                        <TextInput
                            style={styles.input}
                            value={email}
                            onChangeText={setEmail}
                            placeholder="Enter your email"
                            keyboardType="email-address"
                            autoCapitalize="none"
                        />
                    </View>

                    <View style={styles.inputContainer}>
                        <Text style={styles.label}>Password</Text>
                        <TextInput
                            style={styles.input}
                            value={password}
                            onChangeText={setPassword}
                            placeholder="Enter your password"
                            secureTextEntry
                        />
                    </View>

                    {!isLogin && (
                        <View style={styles.inputContainer}>
                            <Text style={styles.label}>Confirm Password</Text>
                            <TextInput
                                style={styles.input}
                                value={confirmPassword}
                                onChangeText={setConfirmPassword}
                                placeholder="Confirm your password"
                                secureTextEntry
                            />
                        </View>
                    )}

                    <TouchableOpacity
                        style={styles.button}
                        onPress={handleSubmit}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator color="#fff" />
                        ) : (
                            <Text style={styles.buttonText}>{isLogin ? 'Login' : 'Register'}</Text>
                        )}
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.switchButton}
                        onPress={() => setIsLogin(!isLogin)}
                    >
                        <Text style={styles.switchText}>
                            {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
                        </Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    scrollContent: {
        flexGrow: 1,
        justifyContent: 'center',
        padding: 20,
    },
    header: {
        alignItems: 'center',
        marginBottom: 40,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 10,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
    },
    form: {
        width: '100%',
    },
    inputContainer: {
        marginBottom: 20,
    },
    label: {
        fontSize: 14,
        color: '#333',
        marginBottom: 5,
        fontWeight: '500',
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        backgroundColor: '#fafafa',
    },
    button: {
        backgroundColor: '#007AFF',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 10,
    },
    buttonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold',
    },
    switchButton: {
        marginTop: 20,
        alignItems: 'center',
    },
    switchText: {
        color: '#007AFF',
        fontSize: 14,
    },
});

export default AuthScreen;
