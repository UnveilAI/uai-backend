from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_service import gemini_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CodePayload(BaseModel):
    code: str

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
