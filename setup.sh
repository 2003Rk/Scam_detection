#!/bin/bash

echo "🎤 ScamShield Voice Analyzer Setup"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip3 found"

# Install system dependencies (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📦 Installing system dependencies for macOS..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install audio dependencies
    brew install portaudio ffmpeg
    echo "✅ System dependencies installed"
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv voice_analyzer_env

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source voice_analyzer_env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 To start the voice analyzer:"
echo "  1. Activate the environment: source voice_analyzer_env/bin/activate"
echo "  2. Start the server: python3 voice_analyzer.py"
echo "  3. The API will be available at: http://localhost:5000"
echo ""
echo "🌐 Your frontend will connect to this local server for voice analysis."