# Hoppi Mobile App

A React Native mobile app that turns the real world into your playground!

## 🚀 Features

- 📍 **GPS Location Detection** - Works on mobile devices
- 🎯 **Location-based Tasks** - Get creative tasks based on your location
- 📸 **Camera Integration** - Take photos, videos, and record audio
- 🎵 **Social Tasks** - Connect with strangers through fun activities
- 📱 **Native Performance** - Smooth mobile experience

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### For Android:
- [Node.js](https://nodejs.org/) (v16 or later)
- [React Native CLI](https://reactnative.dev/docs/environment-setup)
- [Android Studio](https://developer.android.com/studio)
- [Java Development Kit (JDK)](https://www.oracle.com/java/technologies/downloads/) (JDK 11 or later)

### For iOS (Mac only):
- [Xcode](https://developer.apple.com/xcode/)
- [CocoaPods](https://cocoapods.org/)

## 🛠️ Installation

1. **Clone and navigate to the mobile directory:**
   ```bash
   cd mobile
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **For iOS (Mac only):**
   ```bash
   cd ios && pod install && cd ..
   ```

## 🏃‍♂️ Running the App

### Android:
```bash
# Start Metro bundler
npm start

# In another terminal, run on Android
npm run android
```

### iOS (Mac only):
```bash
# Start Metro bundler
npm start

# In another terminal, run on iOS
npm run ios
```

## 📱 Building for Production

### Android APK:
```bash
# Debug APK
cd android && ./gradlew assembleDebug

# Release APK
cd android && ./gradlew assembleRelease
```

The APK will be generated in `android/app/build/outputs/apk/`

### iOS (Mac only):
```bash
# Build for iOS
npm run build-ios
```

## 🔧 Troubleshooting

### Location Not Working:
1. Make sure location permissions are enabled in your device settings
2. Try running the app in a different location
3. Check if GPS is enabled on your device

### Build Issues:
1. Clean and rebuild:
   ```bash
   # Android
   cd android && ./gradlew clean && cd ..
   npm run android
   
   # iOS
   cd ios && xcodebuild clean && cd ..
   npm run ios
   ```

2. Reset Metro cache:
   ```bash
   npm start -- --reset-cache
   ```

## 📦 Dependencies

- **React Native** - Mobile framework
- **Geolocation** - GPS location detection
- **Permissions** - Handle device permissions
- **Camera** - Photo and video capture
- **Audio Recorder** - Audio recording
- **Linear Gradient** - Beautiful UI gradients

## 🎯 How to Use

1. **Open the app** on your mobile device
2. **Allow location access** when prompted
3. **Get your adventure task** based on your location
4. **Capture your moment** using camera, video, or audio
5. **Share your experience** with others

## 📱 Supported Platforms

- ✅ Android 6.0+ (API level 23+)
- ✅ iOS 11.0+
- ✅ Both phones and tablets

## 🔒 Permissions Required

- **Location** - To generate location-based tasks
- **Camera** - To take photos and videos
- **Microphone** - To record audio
- **Storage** - To save captured media

## 🎨 Customization

You can customize the app by modifying:
- `App.js` - Main app logic and UI
- `styles` - Visual styling and themes
- `TASKS_BY_LOCATION` - Task generation logic

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Make sure all dependencies are properly installed
3. Verify your device meets the minimum requirements

Happy adventuring with Hoppi! 🎉
