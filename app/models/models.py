from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime


class RepositorySource(str, Enum):
    GITHUB = "github"
    LOCAL = "local"
    ZIP = "zip"
    GIT = "git"


class RepositoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    source: RepositorySource
    source_url: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    pass


class Repository(RepositoryBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    file_count: int = 0
    language_stats: Dict[str, int] = {}
    status: str = "pending"

    class Config:
        orm_mode = True


class QuestionBase(BaseModel):
    repository_id: UUID
    question: str
    context: Optional[str] = None
    phone: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(BaseModel):
    text_response: str
    audio_url: Optional[str] = None
    code_snippets: List[Dict[str, Any]] = []
    references: List[Dict[str, Any]] = []


class Question(QuestionBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    response: Optional[QuestionResponse] = None

    class Config:
        orm_mode = True


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


class AudioRequest(BaseModel):
    text: str
    format: AudioFormat = AudioFormat.MP3
    voice_id: Optional[str] = None


class AudioResponse(BaseModel):
    audio_url: str
    duration_seconds: float
    format: AudioFormat


class VectorStoreItem(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None

class PhoneCallRequest(BaseModel):
    phone_number: str
    knowledge_base_name: Optional[str] = None
    knowledge_base_description: Optional[str] = None
    knowledge_base_text: Optional[str] = None
    knowledge_base_id: Optional[str] = None  # vector_id from previously created knowledge base
    call_instructions: Optional[str] = None  # task in Bland API
    voice_id: Optional[str] = None  # voice in Bland API
    background_track: Optional[str] = None
    first_sentence: Optional[str] = None
    wait_for_greeting: Optional[bool] = False
    block_interruptions: Optional[bool] = False
    language: Optional[str] = "en-US"
    record: Optional[bool] = False

class PhoneCallResponse(BaseModel):
    call_id: str
    status: str
    phone_number: str
    knowledge_base_id: Optional[str] = None