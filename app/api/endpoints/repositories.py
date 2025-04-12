import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models.models import Repository, RepositoryCreate, RepositorySource
from app.services.repository_service import repository_service
from app.core.config import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Repository)
async def create_repository(
        background_tasks: BackgroundTasks,
        name: str = Form(...),
        description: Optional[str] = Form(None),
        source: RepositorySource = Form(...),
        source_url: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None)
):
    """
    Create a new repository from different sources (GitHub, ZIP, etc.).
    """
    try:
        # Generate a unique ID for the repository
        repository_id = str(uuid.uuid4())

        # Create repository data
        repository = Repository(
            id=repository_id,
            name=name,
            description=description,
            source=source,
            source_url=source_url,
            status="processing"
        )

        # Process based on the source type
        if source == RepositorySource.GITHUB or source == RepositorySource.GIT:
            if not source_url:
                raise HTTPException(status_code=400, detail="Source URL is required for GitHub/Git repositories")

            # Clone the repository in the background
            background_tasks.add_task(
                _process_git_repository,
                source_url,
                repository_id,
                repository
            )

        elif source == RepositorySource.ZIP:
            if not file:
                raise HTTPException(status_code=400, detail="File upload is required for ZIP repositories")

            # Save the uploaded file
            file_path = os.path.join(settings.TEMP_DIR, f"{repository_id}.zip")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Process the ZIP file in the background
            background_tasks.add_task(
                _process_zip_repository,
                file_path,
                repository_id,
                repository
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported repository source: {source}")

        return repository

    except Exception as e:
        logger.error(f"Error creating repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Repository])
async def list_repositories():
    """
    List all repositories.
    """
    # This would typically query a database
    # For now, return an empty list as we don't have persistent storage
    return []


@router.get("/{repository_id}", response_model=Repository)
async def get_repository(repository_id: str):
    """
    Get a specific repository by ID.
    """
    # This would typically query a database
    # For now, check if the repository directory exists
    repo_dir = settings.UPLOAD_DIR / repository_id
    if not repo_dir.exists():
        raise HTTPException(status_code=404, detail="Repository not found")

    # Return basic info since we don't have persistent storage
    return Repository(
        id=repository_id,
        name="Repository",
        source=RepositorySource.GITHUB,
        status="ready"
    )


@router.get("/{repository_id}/files")
async def get_repository_files(repository_id: str, filter: Optional[str] = None):
    """
    Get files in a repository, optionally filtered by extension.
    """
    try:
        files = await repository_service.get_repository_files(repository_id, filter)
        return {"files": files}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Repository not found")
    except Exception as e:
        logger.error(f"Error getting repository files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/files/{file_path:path}")
async def get_file_content(repository_id: str, file_path: str):
    """
    Get the content of a specific file in a repository.
    """
    try:
        content = await repository_service.get_file_content(repository_id, file_path)
        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{repository_id}")
async def delete_repository(repository_id: str):
    """
    Delete a repository.
    """
    try:
        success = await repository_service.delete_repository(repository_id)
        if success:
            return JSONResponse(content={"detail": "Repository deleted successfully"})
        else:
            raise HTTPException(status_code=404, detail="Repository not found")
    except Exception as e:
        logger.error(f"Error deleting repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions
async def _process_git_repository(source_url: str, repository_id: str, repository: Repository):
    """
    Process a Git repository in the background.
    """
    try:
        repo_info = await repository_service.clone_git_repository(source_url, repository_id)

        # Update repository with info
        # In a real implementation, this would update the database
        repository.status = "ready"
        repository.file_count = repo_info["file_count"]
        repository.language_stats = repo_info["language_stats"]

        logger.info(f"Repository {repository_id} processed successfully")

    except Exception as e:
        logger.error(f"Error processing Git repository: {str(e)}")
        repository.status = "error"
        # In a real implementation, this would update the database


async def _process_zip_repository(file_path: str, repository_id: str, repository: Repository):
    """
    Process a ZIP repository in the background.
    """
    try:
        repo_info = await repository_service.upload_zip_repository(file_path, repository_id)

        # Update repository with info
        # In a real implementation, this would update the database
        repository.status = "ready"
        repository.file_count = repo_info["file_count"]
        repository.language_stats = repo_info["language_stats"]

        logger.info(f"Repository {repository_id} processed successfully")

    except Exception as e:
        logger.error(f"Error processing ZIP repository: {str(e)}")
        repository.status = "error"
        # In a real implementation, this would update the database