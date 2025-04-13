from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.gemini_service import gemini_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CodePayload(BaseModel):
    code: str

class QuestionPayload(BaseModel):
    question: str
    code_context: Optional[str] = None
    repository_info: Optional[Dict[str, Any]] = None

@router.post("/explain")
async def explain_code(payload: CodePayload):
    """
    Explain code using the Gemini model.
    """
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="No code provided.")
    
    # Call your Gemini service
    analysis = await gemini_service.analyze_code(payload.code)
    
    # If analyze_code returns a text, wrap it in JSON, e.g. { "explanation": "..."}
    return {"explanation": analysis}

@router.post("/answer")
async def answer_question(payload: QuestionPayload):
    """
    Answer a question about code using the Gemini model.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="No question provided.")
    
    # Call your Gemini service
    answer = await gemini_service.answer_question(
        question=payload.question,
        code_context=payload.code_context,
        repository_info=payload.repository_info
    )
    
    # Return the answer from the service
    return {"answer": answer}