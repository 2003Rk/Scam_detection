#!/usr/bin/env python3
"""
Voice Analyzer Backend for ScamShield
Uses free Python libraries for audio analysis and scam detection
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import librosa
import numpy as np
import speech_recognition as sr
import tempfile
import re
from werkzeug.utils import secure_filename
import logging

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

def analyze_audio_features(audio_path):
    """Analyze audio features for suspicious characteristics"""
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, duration=60)  # Limit to 60 seconds
        
        # Extract features
        features = {}
        
        # Speech rate (syllables per second approximation)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        speech_rate = len(onset_frames) / len(y) * sr
        features['speech_rate'] = float(speech_rate)
        
        # Pitch analysis
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
        pitch_std = np.std(pitches[pitches > 0]) if np.any(pitches > 0) else 0
        features['pitch_mean'] = float(pitch_mean)
        features['pitch_variation'] = float(pitch_std)
        
        # Energy/volume analysis
        rms = librosa.feature.rms(y=y)[0]
        features['volume_mean'] = float(np.mean(rms))
        features['volume_variation'] = float(np.std(rms))
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        features['spectral_centroid'] = float(np.mean(spectral_centroids))
        
        # Zero crossing rate (indicates speech vs noise)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        features['zero_crossing_rate'] = float(np.mean(zcr))
        
        return features
        
    except Exception as e:
        logger.error(f"Audio analysis error: {str(e)}")
        return {}

def transcribe_audio(audio_path):
    """Transcribe audio to text using speech recognition"""
    recognizer = sr.Recognizer()
    
    try:
        # Convert to WAV if needed and load
        with sr.AudioFile(audio_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)
        
        # Try multiple recognition methods
        text = ""
        
        # Try Google Speech Recognition (free tier)
        try:
            text = recognizer.recognize_google(audio)
            logger.info("Successfully transcribed with Google Speech Recognition")
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            
            # Fallback to offline recognition
            try:
                text = recognizer.recognize_sphinx(audio)
                logger.info("Successfully transcribed with Sphinx (offline)")
            except sr.UnknownValueError:
                logger.warning("Sphinx could not understand audio")
            except sr.RequestError as e:
                logger.error(f"Sphinx recognition error: {e}")
        
        return text.lower() if text else ""
        
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

def analyze_audio_characteristics(features):
    """Analyze audio characteristics for suspicious traits"""
    suspicion_score = 0
    audio_indicators = []
    
    if not features:
        return {"audio_score": 0, "audio_indicators": ["Could not analyze audio features"]}
    
    # Check speech rate (too fast might indicate script reading)
    speech_rate = features.get('speech_rate', 0)
    if speech_rate > 8:  # Very fast speech
        suspicion_score += 15
        audio_indicators.append("Unusually fast speech rate detected")
    elif speech_rate > 6:
        suspicion_score += 10
        audio_indicators.append("Fast speech rate detected")
    
    # Check pitch variation (monotone might indicate script reading)
    pitch_variation = features.get('pitch_variation', 0)
    if pitch_variation < 20:  # Very monotone
        suspicion_score += 10
        audio_indicators.append("Monotone speech pattern (possible script reading)")
    
    # Check volume consistency (too consistent might be artificial)
    volume_variation = features.get('volume_variation', 0)
    if volume_variation < 0.01:  # Very consistent volume
        suspicion_score += 5
        audio_indicators.append("Unusually consistent volume levels")
    
    return {
        "audio_score": min(suspicion_score, 100),
        "audio_indicators": audio_indicators
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Voice Analyzer API is running"})

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
            # Analyze audio features
            logger.info("Analyzing audio features...")
            audio_features = analyze_audio_features(temp_path)
            
            # Transcribe audio
            logger.info("Transcribing audio...")
            transcribed_text = transcribe_audio(temp_path)
            
            # Analyze text for scams
            logger.info("Analyzing text for scam indicators...")
            text_analysis = analyze_text_for_scams(transcribed_text)
            
            # Analyze audio characteristics
            logger.info("Analyzing audio characteristics...")
            audio_analysis = analyze_audio_characteristics(audio_features)
            
            # Combine scores
            total_score = (text_analysis["scam_score"] * 0.7) + (audio_analysis["audio_score"] * 0.3)
            
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
                "audio_features": audio_features,
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
    print("  • Audio feature analysis (pitch, rate, volume)")
    print("  • Speech-to-text transcription")
    print("  • Scam keyword detection")
    print("  • Risk assessment")
    print("\n🚀 Server starting on http://localhost:5000")
    print("📝 API endpoint: POST /analyze")
    
    app.run(host='0.0.0.0', port=5000, debug=True)