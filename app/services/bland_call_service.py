import httpx
import logging
from typing import Dict, List, Any, Optional
from app.core.settings import settings  # Changed from app.core.config to app.core.settings
from app.models.models import VectorStoreItem

# Configure logging
logger = logging.getLogger(__name__)


class BlandService:
    def __init__(self):
        self.api_key = settings.BLAND_API_KEY
        self.api_url = settings.BLAND_API_URL
        logger.info("Initialized Bland AI service")

    headers = { authorization = f"{self.api_key}", }
    async def create_knowledge_base(self, name: str, description: str, text: str) -> str:
        """
        Create a knowledge base in Bland AI.
        
        Args:
            name: The name of the knowledge base
            description: A description of the knowledge base
            text: The full text document to be stored and vectorized
            
        Returns:
            Knowledge base ID (vector_id)
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "authorization": f"{self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "name": name,
                    "description": description,
                    "text": text
                }
                
                response = await client.post(
                    f"{self.api_url}/knowledgebases",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                return response_data["vector_id"]
                
        except Exception as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            raise

    async def make_phone_call(
        self, 
        phone_number: str, 
        task: Optional[str] = None,
        voice: Optional[str] = None,
        background_track: Optional[str] = None,
        first_sentence: Optional[str] = None,
        wait_for_greeting: Optional[bool] = False,
        block_interruptions: Optional[bool] = False,
        language: Optional[str] = "en-US",
        record: Optional[bool] = False,
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Make a phone call using Bland AI.
        
        Args:
            phone_number: The phone number to call (required)
            task: Instructions for the AI agent (required if not using pathway_id)
            voice: Voice ID for the call
            background_track: Background audio track
            first_sentence: First sentence the AI should say
            wait_for_greeting: Whether to wait for greeting
            block_interruptions: Whether to block interruptions
            language: Language for the call
            record: Whether to record the call
            tools: List of tools (including knowledge base IDs) to use
            
        Returns:
            Dictionary with call information
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "authorization": f"{self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "phone_number": phone_number
                }
                
                if task:
                    payload["task"] = task
                    
                if voice:
                    payload["voice"] = voice
                    
                if background_track:
                    payload["background_track"] = background_track
                    
                if first_sentence:
                    payload["first_sentence"] = first_sentence
                    
                if wait_for_greeting:
                    payload["wait_for_greeting"] = wait_for_greeting
                    
                if block_interruptions:
                    payload["block_interruptions"] = block_interruptions
                    
                if language:
                    payload["language"] = language
                    
                if record:
                    payload["record"] = record
                    
                if tools:
                    payload["tools"] = tools
                
                response = await client.post(
                    f"{self.api_url}/calls",
                    headers=headers,
                    json=payload
                )

                print(self.api_url)
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error making phone call: {str(e)}")
            raise

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        Get the status of a phone call.
        
        Args:
            call_id: The ID of the call to get the status for
            
        Returns:
            Dictionary with call information
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "authorization": f"{self.api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.get(
                    f"{self.api_url}calls/{call_id}",
                    headers=headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            raise


# Create a singleton instance
bland_service = BlandService()