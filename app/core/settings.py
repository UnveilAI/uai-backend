from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    SECRET_KEY: str = "your-secure-secret-key-change-me-KEEPHIDDEN"
    
    # Google Gemini API settings
    GEMINI_API_KEY: str = "your_gemini_api_key"
    GEMINI_MODEL: str = "your_gemini_model"
    
    # Storage settings
    MAX_UPLOAD_SIZE_MB: int = 80
    UPLOAD_DIR: Path = Path("./uploads")
    TEMP_DIR: Path = Path("./temp")
    
    # Audio settings
    AUDIO_FORMAT: str = "mp3"
    AUDIO_QUALITY: str = "medium"
    AUDIO_DIR: Path = Path("./audio")
    
    class Config:
        env_file = ".env"

settings = Settings()
