#!/bin/bash

echo "🎤 Starting ScamShield Voice Analyzer Backend..."
echo "==============================================="

# Check if virtual environment exists
if [ ! -d "voice_analyzer_env" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first:"
    echo "   ./setup.sh"
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source voice_analyzer_env/bin/activate

# Check if Python backend exists
if [ ! -f "voice_analyzer.py" ]; then
    echo "❌ voice_analyzer.py not found!"
    exit 1
fi

echo "🚀 Starting Python backend server..."
echo "📍 Server will be available at: http://localhost:5000"
echo "📝 API endpoint: POST /analyze"
echo ""
echo "💡 To test the server, open your ScamShield web app and upload an audio file."
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Python server
python3 voice_analyzer.py