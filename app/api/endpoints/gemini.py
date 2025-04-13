from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.gemini_service import gemini_service
from app.services.repository_service import repository_service
from app.services.bland_call_service import bland_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ExplainRequest(BaseModel):
    code: str
    question: Optional[str] = None
    repository_id: Optional[str] = None
    phone_number: Optional[str] = None

class ExplainResponse(BaseModel):
    explanation: str

@router.post("/explain", response_model=ExplainResponse)
async def explain_code(request: ExplainRequest):
    try:
        # CASE 1: File explanation mode
        if request.code != "ENTIRE_CODEBASE":
            prompt = ""
            if request.question:
                prompt = f"""
                You're an expert senior developer. A junior developer has asked:
                "{request.question}"

                Here's the code:
                ```
                {request.code}
                ```

                Provide an insightful, practical explanation with:
                - Direct answer first
                - Security or bug concerns
                - Best practices
                - Expert context

                Format as JSON:
                {{
                    "text_response": "...",
                    "code_snippets": [...],
                    "references": [...]
                }}
                """
            else:
                prompt = f"""
                Here's some code:
                ```
                {request.code}
                ```

                Give a high-level explanation with:
                - What it does
                - Any security or performance issues
                - Suggested improvements

                Format as JSON:
                {{
                    "text_response": "...",
                    "code_snippets": [...],
                    "references": [...]
                }}
                """

            response = await gemini_service.answer_question(
                question=request.question or "Explain this code",
                code_context=request.code,
                repository_info={"name": "Current Repository"},
                custom_prompt=prompt
            )

            return ExplainResponse(explanation=response)

        # CASE 2: Entire repo analysis mode
        if not request.repository_id:
            raise HTTPException(status_code=400, detail="Repository ID is required for full codebase explanation.")

        files = await repository_service.get_repository_files(request.repository_id)
        all_files = files.get("files", [])
        key_patterns = [
            "main", "config", "auth", "security", "database", "models", "app",
            "index", "server", "api", "routes", "env", "docker", "settings"
        ]

        key_files = [f for f in all_files if any(p in f['path'].lower() for p in key_patterns)]
        other_files = [f for f in all_files if f not in key_files]

        selected_files = key_files[:5] + other_files[:5]

        file_contents = []
        for f in selected_files:
            try:
                content = await repository_service.get_file_content(request.repository_id, f['path'])
                file_contents.append({
                    "path": f['path'],
                    "content": content.get("content", "")[:1500]
                })
            except Exception as e:
                logger.warning(f"Failed to read {f['path']}: {str(e)}")

        codebase_prompt = f"""
        You're onboarding a new developer. Below are key files from the codebase:

        {chr(10).join([f"File: {fc['path']}\n```\n{fc['content']}\n```" for fc in file_contents])}

        Provide:
        - High-level architecture overview
        - Key components & interactions
        - Security concerns
        - Suggested improvements
        - What to focus on first

        Format as JSON:
        {{
            "text_response": "...",
            "code_snippets": [...],
            "references": [...]
        }}
        """

        if request.question:
            codebase_prompt += f"\nThe dev asked: \"{request.question}\". Address this specifically."

        response = await gemini_service.answer_question(
            question="Explain this codebase",
            code_context="\n".join([f"{fc['path']}:\n{fc['content'][:500]}" for fc in file_contents]),
            repository_info={"name": "Full Repository"},
            custom_prompt=codebase_prompt
        )

        # Optional: Trigger Bland AI call
        if request.phone_number:
            kb_text = "\n\n".join([f"{f['path']}:\n{f['content']}" for f in file_contents])
            kb_id = await bland_service.create_knowledge_base(
                name="Auto KB - Repo Summary",
                description="Generated from Gemini repo onboarding",
                text=kb_text
            )

            await bland_service.make_phone_call(
                phone_number=request.phone_number,
                task="Explain the codebase to the developer.",
                tools=[kb_id]
            )

        return ExplainResponse(explanation=response)

    except Exception as e:
        logger.error(f"Error in /explain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))