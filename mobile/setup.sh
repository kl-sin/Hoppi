#!/bin/bash

echo "🎯 Setting up Hoppi Mobile App..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "Download from: https://nodejs.org/"
    exit 1
fi

# Check if React Native CLI is installed
if ! command -v react-native &> /dev/null; then
    echo "📦 Installing React Native CLI..."
    npm install -g react-native-cli
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# For iOS (Mac only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Setting up iOS..."
    cd ios && pod install && cd ..
    echo "✅ iOS setup complete!"
fi

echo "✅ Setup complete!"
echo ""
echo "🚀 To run the app:"
echo "   Android: npm run android"
echo "   iOS:     npm run ios"
echo ""
echo "📱 Make sure to:"
echo "   1. Enable Developer Options on your Android device"
echo "   2. Enable USB Debugging"
echo "   3. Allow location permissions when prompted"
echo ""
echo "Happy adventuring! 🎉"
