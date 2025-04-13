from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.gemini_service import gemini_service
from app.services.repository_service import repository_service
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


class ExplainRequest(BaseModel):
    code: str
    question: Optional[str] = None
    repository_id: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str


@router.post("/explain", response_model=ExplainResponse)
async def explain_code(request: ExplainRequest):
    try:
        # If this is for a specific file
        if request.code != "ENTIRE_CODEBASE":
            # Build a human-like, insightful prompt
            if request.question:
                # For specific questions about a file
                prompt = f"""
                You're an expert senior developer who has been with the company for years. 
                A new team member has come to you with some code and a question. 

                They want to know: "{request.question}"

                Here's the code they're asking about:

                ```
                {request.code}
                ```

                As a mentor, provide an insightful, practical explanation that:

                1. Directly answers their question first
                2. Highlights any security concerns or potential bugs you notice
                3. Shares relevant context about how this code fits into typical systems
                4. Offers best practices they should know
                5. Includes insights that would typically take months or years to learn

                Your goal is to accelerate their understanding as if they had years of experience.
                Be conversational but precise - deliver real value that helps them avoid common pitfalls.

                Format your response as JSON with the following structure:
                {{
                    "text_response": "Your detailed explanation here",
                    "code_snippets": [
                        {{"language": "language_name", "code": "improved_code_here", "explanation": "why this is better"}}
                    ],
                    "references": [
                        {{"type": "best_practice/security/pattern", "name": "name_of_reference", "description": "brief actionable description"}}
                    ]
                }}
                """
            else:
                # For general file explanation without a specific question
                prompt = f"""
                You're an expert senior developer who's been asked to help a new team member understand a piece of code.

                Here's the code they need to understand:

                ```
                {request.code}
                ```

                As their mentor, provide an insightful explanation that:

                1. Clearly explains what this code does and its purpose in plain language
                2. Identifies any security concerns, anti-patterns or potential bugs
                3. Highlights patterns or idioms that would be non-obvious to newer developers
                4. Points out any aspects that might cause problems during scaling or maintenance
                5. Suggests improvements that would make this code more robust, secure, or maintainable

                Focus on giving them the insights that typically only come with years of experience.
                Be conversational and engaging, but prioritize practical value over academic descriptions.

                Format your response as JSON with the following structure:
                {{
                    "text_response": "Your detailed explanation here",
                    "code_snippets": [
                        {{"language": "language_name", "code": "improved_code_here", "explanation": "why this is better"}}
                    ],
                    "references": [
                        {{"type": "best_practice/security/pattern", "name": "name_of_reference", "description": "brief actionable description"}}
                    ]
                }}
                """

            # Call the answer_question method
            response = await gemini_service.answer_question(
                question=request.question if request.question else "Explain this code and highlight any concerns",
                code_context=request.code,
                repository_info={"name": "Current Repository", "description": "Project codebase"},
                custom_prompt=prompt  # Pass the custom prompt - you may need to modify your service to accept this
            )

            return ExplainResponse(explanation=response)

        # If this is for the entire codebase
        else:
            if not request.repository_id:
                raise HTTPException(status_code=400, detail="Repository ID is required for codebase analysis")

            try:
                # Get repository files
                files = await repository_service.get_repository_files(request.repository_id)

                # Get key files
                all_files = files.get("files", [])

                # Smart file selection - focus on configuration, main files, and security-sensitive files
                key_file_patterns = [
                    "main", "config", "auth", "security", "database", "models", "app",
                    "index", "server", "api", "routes", "environment", ".env", "docker",
                    "package.json", "requirements.txt", "settings", "middleware"
                ]

                # Prioritize files by importance
                key_files = [f for f in all_files if any(pattern in f['path'].lower() for pattern in key_file_patterns)]
                other_files = [f for f in all_files if f not in key_files]

                # Limit to reasonable number but make sure we get the important ones
                selected_files = key_files[:5] + other_files[:5]

                # Get content of selected files
                file_contents = []

                for file in selected_files:
                    try:
                        content = await repository_service.get_file_content(request.repository_id, file['path'])
                        file_contents.append({
                            "path": file['path'],
                            "content": content.get("content", "")[:1500]  # Limit content size
                        })
                    except Exception as e:
                        logger.warning(f"Could not get content for {file['path']}: {str(e)}")

                # Build a powerful onboarding-focused prompt
                codebase_prompt = f"""
                You're a senior engineering mentor tasked with getting a new developer up to speed on an existing codebase.

                Here's a selection of key files from the codebase they'll be working with:

                {chr(10).join([f"File: {fc['path']}\n```\n{fc['content']}\n```\n" for fc in file_contents])}

                As their mentor, provide an insightful orientation that:

                1. Explains the overall architecture and purpose of this system
                2. Identifies the critical components and how they interact
                3. Highlights security considerations and potential vulnerabilities they should be aware of
                4. Points out any technical debt or areas that need improvement
                5. Offers guidance on best practices specific to this codebase
                6. Provides context that would typically take weeks or months to discover on their own

                Your goal is to accelerate their onboarding by giving them a senior developer's perspective.
                Be conversational but focused on delivering real value - what would YOU want to know on day one?

                Format your response with:
                - A clear high-level overview first
                - Specific security concerns or "watch out for" items
                - Context about patterns or architectural decisions
                - Guidance on what to learn or where to focus based on this specific codebase

                Format your response as JSON with the following structure:
                {{
                    "text_response": "Your detailed onboarding guidance here",
                    "code_snippets": [
                        {{"language": "language_name", "code": "key_code_example", "explanation": "why this is important"}}
                    ],
                    "references": [
                        {{"type": "best_practice/security/pattern", "name": "name_of_reference", "description": "why this is relevant to this codebase"}}
                    ]
                }}
                """

                # If there's a specific question about the codebase
                if request.question:
                    codebase_prompt += f"\n\nThe new developer has specifically asked: '{request.question}'. Make sure to address this in your response."

                # Call the answer_question method
                response = await gemini_service.answer_question(
                    question="Provide an onboarding orientation for this codebase",
                    code_context="\n".join([f"{fc['path']}:\n{fc['content'][:500]}" for fc in file_contents]),
                    repository_info={"name": "Project Codebase", "description": "Full repository analysis"},
                    custom_prompt=codebase_prompt  # Pass the custom prompt
                )

                return ExplainResponse(explanation=response)

            except Exception as e:
                logger.error(f"Error in codebase analysis: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error analyzing codebase: {str(e)}")


class QuestionPayload(BaseModel):
    question: str
    code_context: Optional[str] = None
    repository_info: Optional[Dict[str, Any]] = None

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

@router.post("/answer")
async def answer_question(payload: QuestionPayload):
    """
    Answer a question about code using the Gemini model.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="No question provided.")
    
    # Call your Gemini service
    answer = await gemini_service.answer_question(
        question=payload.question,
        code_context=payload.code_context,
        repository_info=payload.repository_info
    )
    
    # Return the answer from the service
    return {"answer": answer}

