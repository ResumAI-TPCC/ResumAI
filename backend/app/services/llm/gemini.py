"""
Google Gemini LLM Provider Implementation
Using the new google-genai SDK
"""

import json
from typing import Optional

from google import genai

from app.core.config import settings

from .base import BaseLLMProvider, LLMResponse, MatchScoreResult


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider"""

    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def optimize(
        self,
        resume_content: str,
        job_description: str,
        instructions: Optional[str] = None,
    ) -> LLMResponse:
        """Optimize resume content"""
        prompt = f"""You are a professional resume optimization expert. Please optimize the following resume based on the target job description.

Target Job Description:
{job_description}

Original Resume:
{resume_content}

{f"Special Instructions: {instructions}" if instructions else ""}

Please provide the optimized resume content, maintaining a professional format and highlighting skills and experience relevant to the position.
"""

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        return LLMResponse(
            content=response.text,
            model=self.model_name,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }
            if response.usage_metadata
            else None,
        )

    async def analyze(
        self,
        resume_content: str,
        job_description: str,
    ) -> LLMResponse:
        """Analyze resume and generate improvement suggestions"""
        prompt = f"""You are a professional resume analyst. Please analyze how well the following resume matches the target job description and provide improvement suggestions.

Target Job Description:
{job_description}

Resume Content:
{resume_content}

Please provide:
1. Resume strengths analysis
2. Areas that need improvement
3. Specific optimization suggestions
4. Keyword recommendations
"""

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        return LLMResponse(
            content=response.text,
            model=self.model_name,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }
            if response.usage_metadata
            else None,
        )

    async def match(
        self,
        resume_content: str,
        job_description: str,
    ) -> MatchScoreResult:
        """Calculate the match score between resume and job description"""
        prompt = f"""You are a professional recruiting expert. Please evaluate how well the following resume matches the job description.

Job Description:
{job_description}

Resume Content:
{resume_content}

Please return the evaluation result in JSON format:
{{
    "score": a match score between 0.0 and 1.0,
    "explanation": "detailed explanation of the match",
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}

Return only JSON, no other content.
"""

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        # Parse JSON response
        try:
            # Clean up possible markdown code block markers
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            result = json.loads(text.strip())

            return MatchScoreResult(
                score=float(result.get("score", 0.0)),
                explanation=result.get("explanation", ""),
                suggestions=result.get("suggestions", []),
            )
        except (json.JSONDecodeError, KeyError):
            # Return default result if parsing fails
            return MatchScoreResult(
                score=0.5,
                explanation=f"Error parsing response: {response.text}",
                suggestions=["Unable to parse AI response, please try again"],
            )
