"""
Service 3 Demo - Using Real Prompt Example

This demonstrates:
1. Receiving a prompt from upstream
2. Sending to Gemini API (mocked)
3. Parsing response into structured dictionary
4. Returning to downstream
"""

import asyncio
import json

# ============================================================
# 上游给你的 Prompt（真实示例）
# ============================================================

UPSTREAM_PROMPT = """You are a professional resume consultant with expertise in career development and hiring practices. Please analyze the following resume and provide actionable improvement suggestions.

## Resume Content:
John Doe
Software Engineer | San Francisco, CA

Experience:
- Built web applications using React
- Improved system performance by 40%
- Led a team of 5 engineers

Skills: Python, React, AWS

## Instructions:
Analyze the resume thoroughly and provide specific, actionable suggestions for improvement.

Please return your analysis in JSON format with a "suggestions" array. Each suggestion should include:
- category: The category of the suggestion ("content", "skills", "format", "language")
- priority: The priority level ("high", "medium", "low")
- title: A brief title for the suggestion
- description: A detailed description of the issue and why it matters
- example: A specific example of how to implement the improvement
"""

# ============================================================
# Mock Gemini Response（模拟 Gemini 返回的内容）
# ============================================================

MOCK_GEMINI_RESPONSE = """```json
{
  "suggestions": [
    {
      "category": "content",
      "priority": "high",
      "title": "Add quantifiable metrics to all achievements",
      "description": "While you mention '40% improvement', other achievements lack specific numbers. Quantifiable results make your accomplishments more credible.",
      "example": "Instead of 'Built web applications using React', write 'Built 5 production web applications using React, serving 10,000+ daily active users'"
    },
    {
      "category": "content",
      "priority": "high",
      "title": "Expand leadership experience details",
      "description": "Leading a team is a significant achievement that deserves more context about scope and outcomes.",
      "example": "'Led a team of 5 engineers to deliver a customer portal project 2 weeks ahead of schedule, resulting in $50K cost savings'"
    },
    {
      "category": "skills",
      "priority": "medium",
      "title": "Categorize and expand skills section",
      "description": "The skills list is brief. Group by category and add proficiency levels for better readability.",
      "example": "Languages: Python (Advanced), JavaScript (Advanced) | Frameworks: React, Django | Cloud: AWS (EC2, S3, Lambda)"
    },
    {
      "category": "format",
      "priority": "medium",
      "title": "Add professional summary",
      "description": "A 2-3 sentence summary at the top helps recruiters quickly understand your value proposition.",
      "example": "Results-driven Software Engineer with 5+ years of experience building scalable web applications. Proven track record of improving system performance and leading cross-functional teams."
    },
    {
      "category": "language",
      "priority": "low",
      "title": "Use stronger action verbs",
      "description": "Starting bullets with powerful verbs makes achievements more impactful.",
      "example": "Replace 'Built' with 'Architected', 'Engineered', or 'Developed'"
    }
  ]
}
```"""


# ============================================================
# 你的 Service 3 代码
# ============================================================

class MockGeminiProvider:
    """Mock Gemini API (no API key needed)"""
    
    async def generate(self, prompt: str) -> str:
        print("   ⏳ Sending to Gemini API...")
        await asyncio.sleep(1.5)  # Simulate network delay
        print("   ✅ Response received from Gemini")
        return MOCK_GEMINI_RESPONSE


def parse_response(raw_response: str) -> dict:
    """
    Parse Gemini's raw text into structured dictionary.
    This is YOUR core parsing logic!
    """
    # Remove markdown code blocks if present
    text = raw_response.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    # Parse JSON
    return json.loads(text.strip())


# ============================================================
# Demo 流程
# ============================================================

async def run_demo():
    print("\n" + "=" * 70)
    print("🎬 SERVICE 3 DEMO: Take Prompt → Send to LLM → Handle Response")
    print("=" * 70)
    
    # STEP 1: 接收上游 Prompt
    print("\n📍 STEP 1: Receive Prompt from Upstream")
    print("-" * 50)
    print(f"Prompt preview: {UPSTREAM_PROMPT[:100]}...")
    print(f"Prompt length: {len(UPSTREAM_PROMPT)} characters")
    
    # STEP 2: 发送给 Gemini
    print("\n📍 STEP 2: Send to Gemini API")
    print("-" * 50)
    provider = MockGeminiProvider()
    raw_response = await provider.generate(UPSTREAM_PROMPT)
    
    print(f"\n   Raw response preview: {raw_response[:80]}...")
    
    # STEP 3: 解析响应
    print("\n📍 STEP 3: Parse Response into Structured Dictionary")
    print("-" * 50)
    result = parse_response(raw_response)
    
    # STEP 4: 返回给下游
    print("\n📍 STEP 4: Return to Downstream")
    print("-" * 50)
    print("\n📤 OUTPUT (structured dictionary for frontend):\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print(f"""
    Summary:
    • Input:  Prompt string ({len(UPSTREAM_PROMPT)} chars)
    • Output: Structured dict with {len(result['suggestions'])} suggestions
    
    Your Service 3 transformed:
    - Raw text from Gemini → Clean JSON dictionary
    - Messy AI response → Frontend-ready data structure
    """)


if __name__ == "__main__":
    asyncio.run(run_demo())
