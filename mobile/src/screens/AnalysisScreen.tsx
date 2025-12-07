import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const AnalysisScreen: React.FC = () => {
    return (
        <View style={styles.container}>
            <Text style={styles.text}>Analysis Screen Placeholder</Text>
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
    },
});

export default AnalysisScreen;
