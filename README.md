# UnveilAI Backend

A FastAPI backend service that supports analyzing code repositories with Google Gemini and providing text and voice explanations.

## Features

- Repository management:
  - Clone Git/GitHub repositories
  - Upload ZIP repositories
  - Analyze repository structure and files
- Integration with Google Gemini:
  - Ask questions about code
  - Get detailed explanations with code snippets and references
- Voice response generation:
  - Convert text explanations to audio
  - Support for multiple audio formats (MP3, WAV, OGG)
- API endpoints for easy integration with Next.js frontend

## Prerequisites

- Python 3.9+
- Git (for cloning repositories)
- Google Gemini API key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ai-code-explainer-backend.git
cd ai-code-explainer-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Update the `.env` file with your configuration, especially your Gemini API key.

## Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

You can access the Swagger UI documentation at http://localhost:8000/docs

## API Endpoints

### Repository Management

- `POST /api/repositories/`: Create a new repository
- `GET /api/repositories/`: List all repositories
- `GET /api/repositories/{repository_id}`: Get a specific repository
- `GET /api/repositories/{repository_id}/files`: List files in a repository
- `GET /api/repositories/{repository_id}/files/{file_path}`: Get file content
- `DELETE /api/repositories/{repository_id}`: Delete a repository

### Questions and Explanations

- `POST /api/questions/`: Ask a question about code
- `GET /api/questions/{question_id}`: Get a specific question and its response
- `GET /api/questions/repository/{repository_id}`: Get all questions for a repository

### Audio Generation

- `POST /api/audio/generate`: Generate audio from text
- `GET /api/audio/files/{filename}`: Get an audio file
- `DELETE /api/audio/files/{filename}`: Delete an audio file

[//]: # (## Docker Deployment)

[//]: # ()
[//]: # (Build and run using Docker:)

[//]: # ()
[//]: # (```bash)

[//]: # (docker build -t ai-code-explainer .)

[//]: # (docker run -p 8000:8000 --env-file .env ai-code-explainer)

[//]: # (```)

## Next.js Frontend Integration

See the provided examples for how to integrate this backend with a Next.js frontend:

- `api.js`: API client for making requests to the backend
- `CodeExplainer.js`: Example React component for the code explainer UI

## Project Structure

```
/ai-code-explainer-backend
    /app
        /api
            __init__.py
            /endpoints
                __init__.py
                repositories.py
                questions.py
                audio.py
        /core
            __init__.py
            config.py
            security.py
        /services
            __init__.py
            gemini_service.py
            voice_service.py
            repository_service.py
        /models
            __init__.py
            repository.py
            question.py
            response.py
        /utils
            __init__.py
            audio_utils.py
            code_utils.py
        main.py
    /tests
        __init__.py
        /api
        /services
    requirements.txt
    README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.