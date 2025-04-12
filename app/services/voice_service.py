import os
import uuid
import logging
from gtts import gTTS
from pydub import AudioSegment
from pathlib import Path
from app.core.config import settings
from app.models.models import AudioFormat

# Configure logging
logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self):
        self.audio_dir = settings.AUDIO_DIR
        self.base_url = "/api/audio/files"  # URL path where audio files will be served

        # Ensure audio directory exists
        os.makedirs(self.audio_dir, exist_ok=True)

        logger.info(f"Voice service initialized. Audio files will be stored in {self.audio_dir}")

    async def generate_audio(self, text: str, format: AudioFormat = AudioFormat.MP3) -> dict:
        """
        Generate audio from text using gTTS.

        Args:
            text: The text to convert to speech
            format: The audio format to generate

        Returns:
            Dictionary with audio file URL and metadata
        """
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{format.value}"
            filepath = self.audio_dir / filename

            # Generate speech with gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(str(filepath))

            # Get audio duration with pydub
            audio = AudioSegment.from_file(filepath)
            duration_seconds = len(audio) / 1000  # Convert milliseconds to seconds

            # Return audio metadata
            return {
                "audio_url": f"{self.base_url}/{filename}",
                "duration_seconds": duration_seconds,
                "format": format
            }

        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise

    def get_audio_file_path(self, filename: str) -> Path:
        """
        Get the full path for an audio file.

        Args:
            filename: The filename of the audio file

        Returns:
            Path object for the audio file
        """
        return self.audio_dir / filename

    async def delete_audio(self, filename: str) -> bool:
        """
        Delete an audio file.

        Args:
            filename: The filename of the audio file to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            filepath = self.get_audio_file_path(filename)
            if filepath.exists():
                os.remove(filepath)
                logger.info(f"Deleted audio file: {filename}")
                return True
            else:
                logger.warning(f"Audio file not found: {filename}")
                return False
        except Exception as e:
            logger.error(f"Error deleting audio file {filename}: {str(e)}")
            return False


# Create a singleton instance
voice_service = VoiceService()