import React from 'react';
import { View, Text, StyleSheet, Button } from 'react-native';
import { apiService } from '../services/api';

const ProfileScreen: React.FC = () => {
    const handleLogout = async () => {
        // This assumes App.tsx handles state change on logout, but App.tsx passes onLogin but not onLogout to screens explicitly.
        // However, App.tsx state change logic might rely on apiService state?
        // Actually App.tsx has its own handleLogout.
        // In a real app we would use Context or Redux/Zustand.
        // For now, let's just call apiService logout and reload app or let App.tsx polling handle it?
        // App.tsx doesn't poll. It checks on mount.
        // So this button might not update UI immediately without context.
        await apiService.logoutApi();
        // In a real implementation we would trigger an event or use a global store.
    };

    return (
        <View style={styles.container}>
            <Text style={styles.text}>Profile Screen Placeholder</Text>
            <Button title="Logout (Demo)" onPress={handleLogout} />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    text: {
        fontSize: 20,
        marginBottom: 20,
    },
});

export default ProfileScreen;
