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
            # Log the request details for debugging
            logger.info(f"Creating knowledge base with name: {name}")
            logger.info(f"Text length: {len(text)} characters")
            logger.info(f"Using Bland API URL: {self.api_url}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {
                    "authorization": f"{self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "name": name,
                    "description": description,
                    "text": text
                }

                # Make the API call with more detailed logging
                logger.info(f"Sending request to {self.api_url}/knowledgebases")
                response = await client.post(
                    f"{self.api_url}/knowledgebases",
                    headers=headers,
                    json=payload
                )

                # Log the response status and contents
                logger.info(f"Knowledge base creation response status: {response.status_code}")

                # Check if the request was successful
                response.raise_for_status()

                # Parse the response JSON
                response_data = response.json()
                logger.info(f"Knowledge base creation response: {response_data}")

                # Check if vector_id exists in the response
                if "vector_id" not in response_data:
                    logger.error(f"Missing vector_id in response: {response_data}")
                    # Try to use an alternative field if available
                    if "id" in response_data:
                        logger.info(f"Using 'id' field instead of 'vector_id': {response_data['id']}")
                        return response_data["id"]
                    raise ValueError(f"Response doesn't contain vector_id: {response_data}")

                return response_data["vector_id"]

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating knowledge base: {e.response.status_code} - {e.response.text}")
            # For debugging, let's see what the response actually contains
            logger.error(f"Response content: {e.response.text}")
            # Check if we can bypass knowledge base creation for testing
            raise Exception(f"Bland API error creating knowledge base: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            raise

    async def make_phone_call(
            self,
            phone_number: str,
            task: Optional[str] = None,
            voice: Optional[str] = None,  # This accepts voice_id from the request
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
            voice: Voice ID for the call (passed as voice_id from the request)
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
            # Log debug information
            logger.info(f"Making phone call to {phone_number}")
            logger.info(f"Using Bland API URL: {self.api_url}")
            logger.info(f"API Key set: {bool(self.api_key)}")

            # Clean up phone number (remove spaces)
            phone_number = phone_number.replace(" ", "")

            async with httpx.AsyncClient() as client:
                headers = {
                    "authorization": f"{self.api_key}",
                    "Content-Type": "application/json"
                }

                # Build the payload
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

                # Boolean parameters
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

                # Log the full request for debugging
                logger.info(f"Sending request to Bland API: {self.api_url}/calls")
                logger.info(f"Payload: {payload}")

                # Make the API call
                response = await client.post(
                    f"{self.api_url}/calls",
                    headers=headers,
                    json=payload,
                    timeout=30.0  # Add a reasonable timeout
                )

                # Check for success
                response.raise_for_status()
                result = response.json()
                logger.info(f"Call initiated successfully: {result}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error making phone call: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Bland API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error making phone call: {str(e)}")
            raise Exception(f"Connection error: {str(e)}")
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
                    f"{self.api_url}/calls/{call_id}",
                    headers=headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            raise


# Create a singleton instance
bland_service = BlandService()