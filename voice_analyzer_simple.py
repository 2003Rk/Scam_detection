#!/usr/bin/env python3
"""
Voice Analyzer Backend for ScamShield - Simplified Version
Uses basic libraries for text analysis and speech recognition
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import re
from werkzeug.utils import secure_filename
import logging

# Try to import speech recognition, but make it optional
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    print("⚠️  Speech recognition not available. Install with: pip install speechrecognition")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Scam detection keywords and phrases
SCAM_KEYWORDS = [
    'urgent', 'act now', 'limited time', 'congratulations', 'winner', 'free money',
    'tax refund', 'irs', 'government', 'lawsuit', 'arrest warrant', 'police',
    'microsoft tech support', 'virus detected', 'computer infected', 'suspicious activity',
    'verify account', 'confirm identity', 'social security', 'credit card',
    'bank account', 'wire transfer', 'bitcoin', 'cryptocurrency', 'investment opportunity',
    'guaranteed returns', 'risk-free', 'make money fast', 'work from home',
    'lonely', 'romance', 'love you', 'meet you', 'military deployed',
    'inheritance', 'million dollars', 'beneficiary', 'lawyer', 'diplomat',
    'customs', 'airport', 'detained', 'fee required', 'processing fee'
]

SCAM_PATTERNS = [
    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone numbers
    r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',  # SSN pattern
    r'\$[\d,]+\.?\d*',  # Money amounts
    r'\bact\s+within\s+\d+\s+hours?\b',  # Urgency patterns
    r'\bcall\s+back\s+immediately\b',
    r'\bverify\s+your\s+account\b'
]

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def transcribe_audio(audio_path):
    """Transcribe audio to text using speech recognition"""
    if not HAS_SPEECH_RECOGNITION:
        return "Speech recognition not available"
    
    recognizer = sr.Recognizer()
    
    try:
        # Convert to WAV if needed and load
        with sr.AudioFile(audio_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)
        
        # Try Google Speech Recognition (free tier)
        try:
            text = recognizer.recognize_google(audio)
            logger.info("Successfully transcribed with Google Speech Recognition")
            return text
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            return ""
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return ""

def analyze_text_for_scams(text):
    """Analyze transcribed text for scam indicators"""
    if not text:
        return {"scam_score": 0, "indicators": [], "risk_level": "unknown"}
    
    scam_score = 0
    indicators = []
    
    # Check for scam keywords
    for keyword in SCAM_KEYWORDS:
        if keyword.lower() in text.lower():
            scam_score += 10
            indicators.append(f"Scam keyword detected: '{keyword}'")
    
    # Check for scam patterns
    for pattern in SCAM_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            scam_score += 15
            indicators.append(f"Suspicious pattern detected: {pattern}")
    
    # Check for urgency indicators
    urgency_words = ['urgent', 'immediate', 'now', 'quickly', 'hurry', 'deadline']
    urgency_count = sum(1 for word in urgency_words if word in text.lower())
    if urgency_count >= 2:
        scam_score += 20
        indicators.append("High urgency language detected")
    
    # Check for financial requests
    financial_words = ['money', 'payment', 'fee', 'cost', 'price', 'pay', 'send', 'transfer']
    financial_count = sum(1 for word in financial_words if word in text.lower())
    if financial_count >= 3:
        scam_score += 25
        indicators.append("Multiple financial requests detected")
    
    # Determine risk level
    if scam_score >= 50:
        risk_level = "high"
    elif scam_score >= 25:
        risk_level = "medium"
    elif scam_score > 0:
        risk_level = "low"
    else:
        risk_level = "minimal"
    
    return {
        "scam_score": min(scam_score, 100),  # Cap at 100
        "indicators": indicators,
        "risk_level": risk_level,
        "transcribed_text": text
    }

def get_basic_audio_info(file_path):
    """Get basic file information without advanced audio processing"""
    try:
        file_size = os.path.getsize(file_path)
        return {
            "file_size": file_size,
            "file_exists": True
        }
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return {
            "file_size": 0,
            "file_exists": False
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "message": "Voice Analyzer API is running",
        "features": {
            "speech_recognition": HAS_SPEECH_RECOGNITION,
            "text_analysis": True,
            "file_upload": True
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze_voice():
    """Main endpoint for voice analysis"""
    try:
        # Check if file is present
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file format. Supported: WAV, MP3, OGG, FLAC, M4A"}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": "File too large. Maximum size: 50MB"}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)
        
        try:
            # Get basic file info
            logger.info("Getting file information...")
            file_info = get_basic_audio_info(temp_path)
            
            # Transcribe audio if speech recognition is available
            transcribed_text = ""
            if HAS_SPEECH_RECOGNITION:
                logger.info("Transcribing audio...")
                transcribed_text = transcribe_audio(temp_path)
            else:
                logger.warning("Speech recognition not available, skipping transcription")
            
            # Analyze text for scams
            logger.info("Analyzing text for scam indicators...")
            text_analysis = analyze_text_for_scams(transcribed_text)
            
            # Simple audio analysis (just basic info for now)
            audio_analysis = {
                "audio_score": 0,
                "audio_indicators": ["Basic file analysis only - install librosa for advanced audio analysis"]
            }
            
            # Calculate total score (mostly based on text analysis for now)
            total_score = text_analysis["scam_score"]
            
            # Determine overall risk
            if total_score >= 60:
                overall_risk = "high"
                recommendation = "⚠️ HIGH RISK: This appears to be a potential scam. Do not provide any personal information or money."
            elif total_score >= 35:
                overall_risk = "medium"  
                recommendation = "⚠️ MEDIUM RISK: Exercise caution. Verify the caller's identity independently."
            elif total_score >= 15:
                overall_risk = "low"
                recommendation = "ℹ️ LOW RISK: Some suspicious elements detected. Stay alert."
            else:
                overall_risk = "minimal"
                recommendation = "✅ MINIMAL RISK: No significant scam indicators detected."
            
            # Prepare response
            response = {
                "success": True,
                "overall_risk": overall_risk,
                "total_score": round(total_score, 1),
                "recommendation": recommendation,
                "text_analysis": text_analysis,
                "audio_analysis": audio_analysis,
                "audio_features": {},  # Empty for now
                "file_info": {
                    "filename": filename,
                    "size": file_size
                }
            }
            
            logger.info(f"Analysis completed successfully. Risk level: {overall_risk}")
            return jsonify(response)
            
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Analysis failed",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("🎤 Voice Analyzer Backend Starting...")
    print("📋 Features:")
    if HAS_SPEECH_RECOGNITION:
        print("  ✅ Speech-to-text transcription")
    else:
        print("  ❌ Speech-to-text (install speechrecognition)")
    print("  ✅ Scam keyword detection")
    print("  ✅ Risk assessment")
    print("  ❌ Advanced audio analysis (install librosa)")
    print("\n🚀 Server starting on http://localhost:5001")
    print("📝 API endpoint: POST /analyze")
    
    app.run(host='0.0.0.0', port=5001, debug=True)