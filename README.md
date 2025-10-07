# ScamShield Voice Analyzer 🎤

A free, local AI-powered voice analysis system for detecting potential scams in audio recordings. No paid APIs required!

## 🌟 Features

- **Speech-to-Text Transcription**: Uses Google Speech Recognition (free tier)
- **Audio Analysis**: Advanced acoustic feature extraction using librosa
- **Scam Detection**: Smart keyword and pattern matching for common scam phrases
- **Risk Assessment**: Multi-layer analysis combining content and audio characteristics
- **No API Keys**: Completely free solution using local Python backend
- **Privacy Focused**: All analysis happens locally on your machine

## 🚀 Quick Setup

### 1. Install Dependencies

Run the setup script to install all required dependencies:

```bash
./setup.sh
```

This will:
- Install Python dependencies (Flask, librosa, speech_recognition, etc.)
- Set up a virtual environment
- Install system dependencies (PortAudio, FFmpeg) via Homebrew

### 2. Start the Backend Server

```bash
./start_backend.sh
```

The server will start on `http://localhost:5000`

### 3. Open the Web App

Open `index.html` in your browser and navigate to the Voice Analyzer section.

## 📋 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv voice_analyzer_env

# Activate it
source voice_analyzer_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python3 voice_analyzer.py
```

## 🔧 How It Works

### Backend Analysis (Python)
1. **Audio Processing**: Uses librosa to extract acoustic features
2. **Speech Recognition**: Transcribes audio using Google Speech Recognition
3. **Scam Detection**: Analyzes transcription for suspicious keywords and patterns
4. **Audio Characteristics**: Examines speech rate, pitch, volume patterns
5. **Risk Scoring**: Combines text and audio analysis for overall risk assessment

### Frontend Integration (JavaScript)
1. **File Upload**: Handles audio file selection and validation
2. **API Communication**: Sends files to Python backend via REST API
3. **Results Display**: Shows comprehensive analysis results
4. **Error Handling**: Graceful fallback if backend is unavailable

## 🎯 Detection Capabilities

### Scam Keywords Detected:
- Urgency words: "urgent", "immediate", "act now"
- Financial terms: "money", "payment", "fee", "transfer"
- Identity requests: "verify", "confirm", "social security"
- Tech support scams: "Microsoft", "virus", "computer infected"
- Romance scams: "lonely", "love", "military deployed"
- Inheritance scams: "beneficiary", "inheritance", "lawyer"

### Audio Analysis:
- **Speech Rate**: Detects unusually fast speech (script reading)
- **Pitch Variation**: Identifies monotone patterns
- **Volume Consistency**: Flags artificial volume levels
- **Spectral Features**: Analyzes frequency characteristics
- **Zero Crossing Rate**: Measures speech naturalness

## 📊 Risk Levels

- **HIGH RISK (60+)**: Multiple scam indicators detected
- **MEDIUM RISK (35-59)**: Some suspicious elements found  
- **LOW RISK (15-34)**: Minor irregularities detected
- **MINIMAL RISK (<15)**: No significant issues found

## 🔍 API Endpoints

### `POST /analyze`
Analyzes uploaded audio file for scam indicators.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Audio file (WAV, MP3, OGG, FLAC, M4A)

**Response:**
```json
{
  "success": true,
  "overall_risk": "medium",
  "total_score": 45.2,
  "recommendation": "⚠️ MEDIUM RISK: Exercise caution...",
  "text_analysis": {
    "scam_score": 35,
    "indicators": ["Scam keyword detected: 'urgent'"],
    "transcribed_text": "This is urgent..."
  },
  "audio_analysis": {
    "audio_score": 15,
    "audio_indicators": ["Fast speech rate detected"]
  },
  "audio_features": {
    "speech_rate": 6.2,
    "pitch_mean": 180.5,
    "volume_mean": 0.65
  }
}
```

### `GET /health`
Health check endpoint.

## 🛠️ Supported File Formats

- WAV
- MP3  
- OGG
- FLAC
- M4A

Maximum file size: 50MB

## 🚨 Troubleshooting

### Common Issues:

1. **"Cannot connect to Python backend"**
   - Make sure the backend server is running: `./start_backend.sh`
   - Check that port 5000 is not blocked
   - Verify the server shows "Server starting on http://localhost:5000"

2. **Audio transcription fails**
   - Check internet connection (Google Speech Recognition requires internet)
   - Try with clearer audio files
   - Ensure audio file is not corrupted

3. **Installation fails on macOS**
   - Install Xcode command line tools: `xcode-select --install`
   - Install Homebrew if not present
   - Try installing PortAudio manually: `brew install portaudio`

4. **Module import errors**
   - Ensure virtual environment is activated
   - Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

## 📱 Testing the System

1. **Start the backend**: `./start_backend.sh`
2. **Open the web app** in your browser
3. **Navigate to Voice Analyzer** section
4. **Upload a test audio file** (try recording yourself saying "This is urgent, verify your account immediately")
5. **Click analyze** and check the results

## 🔒 Privacy & Security

- All analysis happens locally on your machine
- No data is sent to external services except Google Speech Recognition
- Audio files are automatically deleted after analysis
- No personal information is stored or transmitted

## 💡 Tips for Best Results

- Use clear, uncompressed audio files when possible
- Ensure good audio quality (minimal background noise)
- Test with various types of audio to understand the system's capabilities
- The system works best with English audio content

## 🔄 Updates & Maintenance

To update the system:
1. Pull the latest code
2. Reactivate virtual environment: `source voice_analyzer_env/bin/activate`
3. Update dependencies: `pip install -r requirements.txt --upgrade`
4. Restart the backend

## 📞 Support

If you encounter issues:
1. Check the terminal output for error messages
2. Verify all dependencies are installed correctly
3. Test with the health endpoint: `curl http://localhost:5000/health`
4. Review the browser console for JavaScript errors

---

**Made with ❤️ for digital safety and privacy**