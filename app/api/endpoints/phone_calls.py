from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.models import PhoneCallRequest, PhoneCallResponse
from app.services.bland_call_service import bland_service
from app.core.settings import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=PhoneCallResponse)
async def make_phone_call(request: PhoneCallRequest, background_tasks: BackgroundTasks):
    """
    Make a phone call using Bland AI. You can either provide a knowledge_base_id
    for an existing knowledge base, or create a new one by providing
    knowledge_base_name, knowledge_base_description, and knowledge_base_text.
    """
    try:
        # Check if we need to create a knowledge base
        knowledge_base_id = request.knowledge_base_id

        if not knowledge_base_id and request.knowledge_base_text:
            if not request.knowledge_base_name or not request.knowledge_base_description:
                raise HTTPException(
                    status_code=400,
                    detail="When providing knowledge_base_text, both knowledge_base_name and knowledge_base_description are required"
                )

            try:
                # Try to create a knowledge base from the provided text
                knowledge_base_id = await bland_service.create_knowledge_base(
                    name=request.knowledge_base_name,
                    description=request.knowledge_base_description,
                    text=request.knowledge_base_text
                )
            except Exception as e:
                # Log the error but continue without a knowledge base
                logger.error(f"Failed to create knowledge base: {str(e)}")
                logger.warning("Continuing without knowledge base - will use direct instructions instead")
                knowledge_base_id = None

        # Prepare task (instructions) for the call
        task = request.call_instructions

        # If knowledge base creation failed but we have text content, add it to the task
        if not knowledge_base_id and request.knowledge_base_text:
            # Create a simplified task that includes part of the content
            if not task:
                task = "You are a senior developer helping explain code to the user."

            # Extract a summary of the content (first few files) to include in the task
            # This is a fallback as we couldn't create a knowledge base
            content_preview = request.knowledge_base_text[:5000]  # Take first 5000 chars as preview
            task += f"\n\nHere's a preview of the code to reference:\n\n{content_preview}\n\n..."

            logger.info("Added content preview to task as fallback for knowledge base")

        # Prepare tools list with knowledge base if available
        tools = None
        if knowledge_base_id:
            tools = [knowledge_base_id]

        if not task and not knowledge_base_id:
            raise HTTPException(
                status_code=400,
                detail="Either call_instructions or a knowledge base (existing or new) is required"
            )

        # Make the phone call
        call_data = await bland_service.make_phone_call(
            phone_number=request.phone_number,
            task=task,
            voice=request.voice_id,
            background_track=request.background_track,
            first_sentence=request.first_sentence,
            wait_for_greeting=request.wait_for_greeting,
            block_interruptions=request.block_interruptions,
            language=request.language,
            record=request.record,
            tools=tools
        )

        return PhoneCallResponse(
            call_id=call_data["call_id"],
            status=call_data["status"],
            phone_number=request.phone_number,
            knowledge_base_id=knowledge_base_id
        )

    except Exception as e:
        logger.error(f"Error making phone call: {str(e)}")

        # More detailed error message
        error_detail = str(e)
        if "vector_id" in error_detail:
            error_detail = "Failed to create knowledge base. This may be due to an invalid API key or API permission issues."

        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/{call_id}")
async def get_call_status(call_id: str):
    """
    Get the status of a phone call.
    """
    # Skip the config-status special case
    if call_id == "config-status":
        return check_bland_config()

    try:
        call_data = await bland_service.get_call_status(call_id)
        return call_data

    except Exception as e:
        logger.error(f"Error getting call status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Separate function for config check (not a route itself)
def check_bland_config():
    """
    Check if Bland AI API configuration is valid.
    """
    try:
        # Check if API key and URL are set
        if not settings.BLAND_API_KEY:
            return {"status": "error", "message": "BLAND_API_KEY not set in environment variables"}

        if not settings.BLAND_API_URL:
            return {"status": "error", "message": "BLAND_API_URL not set in environment variables"}

        # Return the configuration (but mask the actual API key)
        return {
            "status": "ok",
            "config": {
                "bland_api_url": settings.BLAND_API_URL,
                "bland_api_key_set": bool(settings.BLAND_API_KEY),
                "api_key_preview": f"{settings.BLAND_API_KEY[:5]}..." if settings.BLAND_API_KEY and len(
                    settings.BLAND_API_KEY) > 5 else None
            }
        }

    except Exception as e:
        logger.error(f"Error checking Bland config: {str(e)}")
        return {"status": "error", "message": str(e)}