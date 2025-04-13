import os
import uuid
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import git
from collections import Counter
import zipfile
from app.core.settings import settings  # Updated import

# Configure logging
logger = logging.getLogger(__name__)

class RepositoryService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.temp_dir = settings.TEMP_DIR

        # Ensure directories exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        logger.info(f"Repository service initialized. Repositories will be stored in {self.upload_dir}")

    async def create_repository_directory(self, repository_id: str) -> Path:
        """
        Create a directory for a repository.

        Args:
            repository_id: The unique identifier for the repository

        Returns:
            Path to the created directory
        """
        repo_dir = self.upload_dir / repository_id
        os.makedirs(repo_dir, exist_ok=True)
        return repo_dir

    async def clone_git_repository(self, git_url: str, repository_id: str) -> Dict[str, Any]:
        """
        Clone a git repository.

        Args:
            git_url: The URL of the git repository to clone
            repository_id: The unique identifier for the repository

        Returns:
            Dictionary with repository information
        """
        try:
            # Create repository directory
            repo_dir = await self.create_repository_directory(repository_id)

            # Clone the repository
            git.Repo.clone_from(git_url, repo_dir)

            # Analyze repository
            repo_info = await self.analyze_repository(repo_dir)
            repo_info["source_url"] = git_url
            repo_info["status"] = "ready"

            return repo_info

        except Exception as e:
            logger.error(f"Error cloning repository {git_url}: {str(e)}")
            raise

    async def upload_zip_repository(self, file_path: str, repository_id: str) -> Dict[str, Any]:
        """
        Process an uploaded ZIP file containing a repository.

        Args:
            file_path: Path to the uploaded ZIP file
            repository_id: The unique identifier for the repository

        Returns:
            Dictionary with repository information
        """
        try:
            # Create repository directory
            repo_dir = await self.create_repository_directory(repository_id)

            # Extract ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(repo_dir)

            # Analyze repository
            repo_info = await self.analyze_repository(repo_dir)
            repo_info["source_url"] = None
            repo_info["status"] = "ready"

            return repo_info

        except Exception as e:
            logger.error(f"Error processing ZIP repository: {str(e)}")
            raise
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

    async def analyze_repository(self, repo_dir: Path) -> Dict[str, Any]:
        """
        Analyze a repository to extract information.

        Args:
            repo_dir: Path to the repository directory

        Returns:
            Dictionary with repository analysis
        """
        try:
            # Get all files recursively
            all_files = []
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)

            # Count files by extension
            extensions = [os.path.splitext(f)[1][1:].lower() for f in all_files if os.path.splitext(f)[1]]
            language_stats = dict(Counter(extensions))

            # Basic repository information
            repo_info = {
                "file_count": len(all_files),
                "language_stats": language_stats,
            }

            return repo_info

        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            raise

    async def get_repository_files(self, repository_id: str, file_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get files from a repository, optionally filtered by extension.

        Args:
            repository_id: The unique identifier for the repository
            file_filter: Optional filter for file extensions (e.g., "py" for Python files)

        Returns:
            List of dictionaries with file information
        """
        try:
            repo_dir = self.upload_dir / repository_id

            if not repo_dir.exists():
                raise FileNotFoundError(f"Repository {repository_id} not found")

            # Get all files recursively
            files_info = []
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_dir)

                    # Apply filter if specified
                    if file_filter and not file.endswith(f".{file_filter}"):
                        continue

                    # Get file size
                    size = os.path.getsize(file_path)

                    # Get file extension
                    _, extension = os.path.splitext(file)
                    extension = extension[1:] if extension else ""

                    files_info.append({
                        "path": rel_path,
                        "name": file,
                        "size": size,
                        "extension": extension
                    })

            return files_info

        except Exception as e:
            logger.error(f"Error getting repository files: {str(e)}")
            raise

    async def get_file_content(self, repository_id: str, file_path: str) -> str:
        """
        Get the content of a file in a repository.

        Args:
            repository_id: The unique identifier for the repository
            file_path: The path to the file within the repository

        Returns:
            File content as a string
        """
        try:
            repo_dir = self.upload_dir / repository_id
            full_path = repo_dir / file_path

            if not full_path.exists():
                raise FileNotFoundError(f"File {file_path} not found in repository {repository_id}")

            # Read and return file content
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return content

        except Exception as e:
            logger.error(f"Error getting file content: {str(e)}")
            raise

    async def delete_repository(self, repository_id: str) -> bool:
        """
        Delete a repository.

        Args:
            repository_id: The unique identifier for the repository to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            repo_dir = self.upload_dir / repository_id

            if repo_dir.exists():
                shutil.rmtree(repo_dir)
                logger.info(f"Deleted repository: {repository_id}")
                return True
            else:
                logger.warning(f"Repository not found: {repository_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting repository {repository_id}: {str(e)}")
            return False


# Create a singleton instance
repository_service = RepositoryService()