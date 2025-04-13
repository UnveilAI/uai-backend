import os
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import logging
from app.core.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

        # Initialize Gemini API
        genai.configure(api_key=self.api_key)

        # Generate model
        self.model = genai.GenerativeModel(self.model_name)

        logger.info(f"Initialized Gemini service with model: {self.model_name}")

    async def analyze_code(self, code_content: str) -> Dict[str, Any]:
        """
        Analyze code content to extract key information.

        Args:
            code_content: The code content to analyze

        Returns:
            Dictionary with analysis results
        """
        try:
            prompt = f"""
            You are an expert senior developer with years of experience. 
            Analyze the following code with a focus on insights that would help a new team member:

            ```
            {code_content}
            ```

            Provide a practical, insightful analysis that:
            1. Explains what this code does in clear, conversational language
            2. Highlights any potential security vulnerabilities or bugs
            3. Points out non-obvious patterns or design decisions
            4. Identifies maintenance or scaling challenges
            5. Suggests practical improvements

            Format your response as JSON with the following structure:
            {{
                "overview": "A practical explanation of the code's purpose and function",
                "key_components": [
                    {{"name": "component_name", "type": "function/class/etc", "purpose": "description with practical insights"}}
                ],
                "potential_issues": ["vulnerability1", "bug2", "issue3"],
                "suggested_improvements": ["improvement1", "improvement2"]
            }}
            """

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            raise

    async def answer_question(self,
                              question: str,
                              code_context: Optional[str] = None,
                              repository_info: Optional[Dict[str, Any]] = None,
                              custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a question about code using the Gemini model.

        Args:
            question: The question being asked
            code_context: Relevant code snippets for context
            repository_info: Information about the repository
            custom_prompt: Optional custom prompt to override the default

        Returns:
            Dictionary with the answer and related information
        """
        try:
            # Use custom prompt if provided, otherwise build the default prompt
            if custom_prompt:
                full_prompt = custom_prompt
            else:
                # Build the prompt based on available information
                prompt_parts = ["You are a senior developer mentoring a new team member."]

                if repository_info:
                    repo_desc = f"Repository: {repository_info.get('name', 'Unknown')}"
                    if repository_info.get('description'):
                        repo_desc += f" - {repository_info['description']}"
                    prompt_parts.append(repo_desc)

                if code_context:
                    prompt_parts.append(f"Here is the relevant code context:\n```\n{code_context}\n```")

                prompt_parts.append(f"Question: {question}")

                prompt_parts.append("""
                Please provide a clear, practical explanation that would help a developer understand this code.
                Focus on insights that would typically take months or years to discover, and highlight any security 
                considerations or potential bugs.

                Format your response as JSON with the following structure:
                {
                    "text_response": "Your detailed explanation here",
                    "code_snippets": [
                        {"language": "language_name", "code": "code_here", "explanation": "explanation_here"}
                    ],
                    "references": [
                        {"type": "best_practice/security/pattern", "name": "reference_name", "description": "brief_description"}
                    ]
                }
                """)

                # Join all prompt parts
                full_prompt = "\n\n".join(prompt_parts)

            # Generate response from Gemini
            response = self.model.generate_content(full_prompt)

            # Parse and return the response
            return response.text

        except Exception as e:
            logger.error(f"Error answering question with Gemini: {str(e)}")
            raise


# Create a singleton instance
gemini_service = GeminiService()