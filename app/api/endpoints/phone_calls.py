from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.models import PhoneCallRequest, PhoneCallResponse
from app.services.bland_call_service import bland_service
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
            
            # Create a knowledge base from the provided text
            knowledge_base_id = await bland_service.create_knowledge_base(
                name=request.knowledge_base_name,
                description=request.knowledge_base_description,
                text=request.knowledge_base_text
            )
        
        # Prepare task (instructions) for the call
        task = request.call_instructions
        
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{call_id}")
async def get_call_status(call_id: str):
    """
    Get the status of a phone call.
    """
    try:
        call_data = await bland_service.get_call_status(call_id)
        return call_data
            
    except Exception as e:
        logger.error(f"Error getting call status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))