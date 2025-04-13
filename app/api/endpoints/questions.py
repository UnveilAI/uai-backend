import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from app.models.models import Question, QuestionCreate, QuestionResponse
from app.services.gemini_service import gemini_service
from app.services.repository_service import repository_service
from app.services.voice_service import voice_service
import logging
from app.services.bland_service import bland_service  

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Question)
async def create_question(question_create: QuestionCreate):
    """
    Create a new question about a repository.
    """
    try:
        # Check if repository exists
        repo_dir = await repository_service.create_repository_directory(str(question_create.repository_id))
        if not repo_dir.exists():
            raise HTTPException(status_code=404, detail="Repository not found")

        # Create question instance
        question = Question(
            repository_id=question_create.repository_id,
            question=question_create.question,
            context=question_create.context
        )

        # Process the question synchronously (instead of scheduling a background task)
        await _process_question(question)

        return question

    except Exception as e:
        logger.error(f"Error creating question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str):
    """
    Get a specific question by ID.
    """
    # This would typically query a database
    # For now, return a mock response as we don't have persistent storage
    raise HTTPException(status_code=404, detail="Question not found")


@router.get("/repository/{repository_id}", response_model=List[Question])
async def get_repository_questions(repository_id: str):
    """
    Get all questions for a repository.
    """
    # This would typically query a database
    # For now, return an empty list as we don't have persistent storage
    return []


# Background task functions
async def _process_question(question: Question):
    """
    Process a question in the background.
    """
    try:
        # Get relevant code context if specified
        code_context = None
        if question.context:
            try:
                code_context = await repository_service.get_file_content(
                    str(question.repository_id),
                    question.context
                )
            except Exception as e:
                logger.warning(f"Could not get context file: {str(e)}")

        # Get repository information (mock for now)
        repository_info = {
            "name": f"Repository {question.repository_id}",
            "description": "Repository description"
        }

        # Get answer from Gemini
        raw_response = await gemini_service.answer_question(
            question=question.question,
            code_context=code_context,
            repository_info=repository_info
        )

        # Parse the response
        try:
            response_data = json.loads(raw_response)

            # Create text response
            text_response = response_data.get("text_response", "No response generated")

            # Generate audio response
            audio_data = await voice_service.generate_audio(text_response)

            # Create question response
            question.response = QuestionResponse(
                text_response=text_response,
                audio_url=audio_data["audio_url"],
                code_snippets=response_data.get("code_snippets", []),
                references=response_data.get("references", [])
            )

            logger.info(f"Question {question.id} processed successfully")

        except json.JSONDecodeError:
            # If Gemini doesn't return valid JSON, use the raw response
            logger.warning(f"Non-JSON response from Gemini: {raw_response[:100]}...")

            audio_data = await voice_service.generate_audio(raw_response)

            question.response = QuestionResponse(
                text_response=raw_response,
                audio_url=audio_data["audio_url"]
            )

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        # In a real implementation, this would update the database with the error