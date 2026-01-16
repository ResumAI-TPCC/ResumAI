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
        """优化简历内容"""
        prompt = f"""你是一位专业的简历优化专家。请根据目标职位描述优化以下简历。

目标职位描述：
{job_description}

原始简历：
{resume_content}

{f"用户特别要求：{instructions}" if instructions else ""}

请提供优化后的简历内容，保持专业格式，突出与职位相关的技能和经验。
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
        """分析简历并生成改进建议"""
        prompt = f"""你是一位专业的简历分析师。请分析以下简历与目标职位的匹配情况，并提供改进建议。

目标职位描述：
{job_description}

简历内容：
{resume_content}

请提供：
1. 简历优势分析
2. 需要改进的地方
3. 具体的优化建议
4. 关键词建议
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
        """计算简历与职位的匹配度"""
        prompt = f"""你是一位专业的招聘专家。请评估以下简历与职位描述的匹配程度。

职位描述：
{job_description}

简历内容：
{resume_content}

请以 JSON 格式返回评估结果：
{{
    "score": 0.0-1.0之间的匹配分数,
    "explanation": "详细的匹配度解释",
    "suggestions": ["改进建议1", "改进建议2", "改进建议3"]
}}

只返回 JSON，不要有其他内容。
"""

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        # 解析 JSON 响应
        try:
            # 清理可能的 markdown 代码块标记
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
            # 如果解析失败，返回默认结果
            return MatchScoreResult(
                score=0.5,
                explanation=f"解析响应时出错: {response.text}",
                suggestions=["无法解析 AI 响应，请重试"],
            )
