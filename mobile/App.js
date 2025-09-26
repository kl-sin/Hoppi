import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Alert,
  Image,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import Geolocation from '@react-native-community/geolocation';
import { request, PERMISSIONS, RESULTS } from 'react-native-permissions';
import LinearGradient from 'react-native-linear-gradient';

const { width, height } = Dimensions.get('window');

const App = () => {
  const [location, setLocation] = useState(null);
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(false);
  const [locationStatus, setLocationStatus] = useState('⏳ Getting your location...');

  // Location-based tasks
  const TASKS_BY_LOCATION = {
    'park': [
      "🌳 Hug a tree and ask a stranger or friend to take your photo!",
      "🍃 Create a beautiful pattern using fallen leaves and photograph it.",
      "🎵 Find a stranger and ask them to sing a simple beat with you (clap, snap, or hum).",
      "📹 Record a 30-second video of you doing your best tree impression.",
      "🌿 Collect 5 different types of leaves and arrange them artistically for a photo.",
    ],
    'restaurant': [
      "🍽️ Order something you've never tried and ask a stranger to guess what it is!",
      "🎵 Create a beat using your utensils and ask someone to join in.",
      "📹 Record a video of you doing a dramatic food review for the camera.",
      "🎤 Sing a song about the food you're eating and ask a stranger to rate it.",
      "📱 Take a video of you teaching someone how to eat the most interesting dish on your table.",
    ],
    'street': [
      "🎨 Find street art and ask a stranger to pose with it for a creative photo.",
      "🎵 Start a beat by clapping and see how many people join in!",
      "📹 Record a video of you doing your best street performer impression.",
      "🎤 Sing a song about the street you're on and ask someone to add a verse.",
      "📱 Take a video of you asking strangers to guess what's in a mystery bag.",
    ],
    'beach': [
      "🏖️ Build a sandcastle and ask a stranger to help you decorate it!",
      "🎵 Create a rhythm using seashells and ask someone to join your beach band.",
      "📹 Record a video of you doing your best mermaid impression in the sand.",
      "🎤 Sing a beach-themed song and ask someone to harmonize with you.",
      "📱 Take a video of you teaching a stranger how to find the perfect seashell.",
    ],
    'mall': [
      "🛍️ Find a stranger and ask them to help you pick the most outrageous outfit!",
      "🎵 Create a beat using items from different stores and ask someone to join in.",
      "📹 Record a video of you doing a fashion show walk and ask someone to judge it.",
      "🎤 Sing a shopping-themed song and ask a stranger to add a verse about their favorite store.",
      "📱 Take a video of you asking strangers to guess what's in your shopping bag.",
    ]
  };

  useEffect(() => {
    getLocation();
  }, []);

  const requestLocationPermission = async () => {
    try {
      const result = await request(PERMISSIONS.ANDROID.ACCESS_FINE_LOCATION);
      return result === RESULTS.GRANTED;
    } catch (error) {
      console.error('Permission request error:', error);
      return false;
    }
  };

  const getLocation = async () => {
    setLocationStatus('⏳ Locating...');
    
    const hasPermission = await requestLocationPermission();
    if (!hasPermission) {
      setLocationStatus('❌ Location permission denied');
      Alert.alert('Permission Required', 'Please enable location access to use Hoppi!');
      return;
    }

    Geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setLocation({ latitude, longitude });
        setLocationStatus(`✅ Location found!\nLat: ${latitude.toFixed(6)}\nLon: ${longitude.toFixed(6)}`);
        generateTask(latitude, longitude);
      },
      (error) => {
        let errorMessage = '❌ Error: ';
        switch (error.code) {
          case 1:
            errorMessage += 'Location access denied';
            break;
          case 2:
            errorMessage += 'Location unavailable';
            break;
          case 3:
            errorMessage += 'Location request timed out';
            break;
          default:
            errorMessage += 'Unknown error occurred';
            break;
        }
        setLocationStatus(errorMessage);
        Alert.alert('Location Error', 'Unable to get your location. Please try again.');
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 10000,
      }
    );
  };

  const getLocationType = (lat, lon) => {
    // Simple location type detection - in a real app you'd use reverse geocoding
    const randomTypes = ['park', 'restaurant', 'street', 'beach', 'mall'];
    return randomTypes[Math.floor(Math.random() * randomTypes.length)];
  };

  const generateTask = (lat, lon) => {
    setLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      const locationType = getLocationType(lat, lon);
      const tasks = TASKS_BY_LOCATION[locationType] || TASKS_BY_LOCATION['street'];
      const randomTask = tasks[Math.floor(Math.random() * tasks.length)];
      
      setTask({
        text: randomTask,
        locationType: locationType,
        coordinates: { lat, lon }
      });
      setLoading(false);
    }, 1500);
  };

  const getNewTask = () => {
    if (location) {
      generateTask(location.latitude, location.longitude);
    }
  };

  const openCamera = () => {
    Alert.alert('Camera', 'Camera feature coming soon! For now, use your phone\'s camera app to capture your moment.');
  };

  const shareTask = () => {
    if (task) {
      Alert.alert('Share', `Share this task: "${task.text}"`);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#667eea" />
      
      <LinearGradient
        colors={['#667eea', '#764ba2']}
        style={styles.gradient}
      >
        <ScrollView contentInsetAdjustmentBehavior="automatic" style={styles.scrollView}>
          <View style={styles.content}>
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.logo}>🎯 Hoppi</Text>
              <Text style={styles.subtitle}>Turn the real world into your playground!</Text>
            </View>

            {/* Location Section */}
            <View style={styles.locationCard}>
              <Text style={styles.cardTitle}>📍 Your Location</Text>
              <Text style={styles.locationStatus}>{locationStatus}</Text>
              <TouchableOpacity style={styles.locationButton} onPress={getLocation}>
                <Text style={styles.buttonText}>📍 Get My Location</Text>
              </TouchableOpacity>
            </View>

            {/* Loading */}
            {loading && (
              <View style={styles.loadingCard}>
                <ActivityIndicator size="large" color="#667eea" />
                <Text style={styles.loadingText}>Generating your adventure task...</Text>
              </View>
            )}

            {/* Task Section */}
            {task && (
              <View style={styles.taskCard}>
                <Text style={styles.cardTitle}>🎯 Your Adventure Task</Text>
                <Text style={styles.taskText}>{task.text}</Text>
                <TouchableOpacity style={styles.taskButton} onPress={getNewTask}>
                  <Text style={styles.buttonText}>🎲 Get New Task</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Action Buttons */}
            {task && (
              <View style={styles.actionCard}>
                <Text style={styles.cardTitle}>📸 Capture Your Moment</Text>
                <View style={styles.buttonRow}>
                  <TouchableOpacity style={styles.actionButton} onPress={openCamera}>
                    <Text style={styles.actionButtonText}>📷 Photo</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.actionButton} onPress={openCamera}>
                    <Text style={styles.actionButtonText}>📹 Video</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.actionButton} onPress={openCamera}>
                    <Text style={styles.actionButtonText}>🎤 Audio</Text>
                  </TouchableOpacity>
                </View>
                <TouchableOpacity style={styles.shareButton} onPress={shareTask}>
                  <Text style={styles.buttonText}>📤 Share Task</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </ScrollView>
      </LinearGradient>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  logo: {
    fontSize: 48,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 18,
    color: 'white',
    textAlign: 'center',
    opacity: 0.9,
  },
  locationCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  taskCard: {
    backgroundColor: '#e8f4fd',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
    borderLeftWidth: 5,
    borderLeftColor: '#667eea',
  },
  actionCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  loadingCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 30,
    marginBottom: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  locationStatus: {
    fontSize: 16,
    color: '#666',
    marginBottom: 15,
    textAlign: 'center',
  },
  taskText: {
    fontSize: 18,
    color: '#333',
    lineHeight: 24,
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 15,
  },
  locationButton: {
    backgroundColor: '#28a745',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    alignItems: 'center',
  },
  taskButton: {
    backgroundColor: '#667eea',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    alignItems: 'center',
  },
  shareButton: {
    backgroundColor: '#6c757d',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    alignItems: 'center',
    marginTop: 15,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  actionButton: {
    backgroundColor: '#f8f9fa',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#667eea',
    minWidth: 80,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#667eea',
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default App;
