import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.models.models import AudioRequest, AudioResponse
from app.services.voice_service import voice_service
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=AudioResponse)
async def generate_audio(audio_request: AudioRequest):
    """
    Generate audio from text.
    """
    try:
        # Generate audio with the voice service
        audio_data = await voice_service.generate_audio(
            text=audio_request.text,
            format=audio_request.format
        )

        return AudioResponse(
            audio_url=audio_data["audio_url"],
            duration_seconds=audio_data["duration_seconds"],
            format=audio_data["format"]
        )

    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{filename}")
async def get_audio_file(filename: str):
    """
    Serve an audio file.
    """
    try:
        file_path = voice_service.get_audio_file_path(filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")

        # Determine the media type based on file extension
        extension = os.path.splitext(filename)[1].lower()
        media_type = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg'
        }.get(extension, 'application/octet-stream')

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error serving audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{filename}")
async def delete_audio_file(filename: str, background_tasks: BackgroundTasks):
    """
    Delete an audio file.
    """
    try:
        # Delete the file in the background
        background_tasks.add_task(voice_service.delete_audio, filename)

        return {"detail": "Audio file deletion scheduled"}

    except Exception as e:
        logger.error(f"Error deleting audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))