"""
Voice API Endpoints
Handle speech-to-text and text-to-speech
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.voice_service import VoiceService
from app.core.security import verify_token

router = APIRouter(prefix="/api/voice", tags=["voice"])
logger = logging.getLogger(__name__)


class SpeechToTextRequest(BaseModel):
    """Speech-to-text request"""
    language: str = "en"


class TextToSpeechRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    language: str = "en"
    voice: str = "alloy"


class TextToSpeechResponse(BaseModel):
    """Text-to-speech response"""
    success: bool
    audio_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/transcribe")
async def transcribe_speech(
    file: UploadFile = File(...),
    language: str = "en",
    token: str = None,
):
    """
    Convert speech to text
    
    Args:
        file: Audio file (MP3, WAV, M4A, FLAC, etc.)
        language: Language code (e.g., 'en', 'es', 'fr')
        token: Authentication token
    
    Returns:
        Transcribed text
    """
    try:
        # Verify authentication
        user_id = await verify_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Read file
        content = await file.read()
        
        # Initialize voice service
        voice_service = VoiceService()
        
        # Transcribe
        result = await voice_service.speech_to_text(
            audio_data=content,
            language=language,
        )
        
        logger.info(f"Transcribed audio for user {user_id}")
        
        return {
            "success": True,
            "text": result.get("text"),
            "language": result.get("language"),
            "confidence": result.get("confidence"),
        }
    
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize", response_model=TextToSpeechResponse)
async def synthesize_speech(
    request: TextToSpeechRequest,
    token: str = None,
):
    """
    Convert text to speech
    
    Args:
        request: Text-to-speech request
        token: Authentication token
    
    Returns:
        Audio URL or file
    """
    try:
        # Verify authentication
        user_id = await verify_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Initialize voice service
        voice_service = VoiceService()
        
        # Synthesize
        result = await voice_service.text_to_speech(
            text=request.text,
            language=request.language,
            voice=request.voice,
        )
        
        logger.info(f"Synthesized speech for user {user_id}")
        
        return TextToSpeechResponse(
            success=True,
            audio_url=result.get("audio_url"),
        )
    
    except Exception as e:
        logger.error(f"Synthesis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
        ],
    }
