"""
Service 3 Demo (Mock Version) - No API Key Required

This demonstrates the SERVICE FLOW without calling real API:
1. Receive prompt from upstream
2. [Mock] Send to LLM
3. Parse response and return structured data

Use this for demos when API key is not available.
"""

import asyncio
import json


# ============================================================
# Mock LLM Response (simulates what Gemini would return)
# ============================================================

MOCK_LLM_RESPONSE = """
Based on my analysis of the resume, here are my suggestions:

1. **Skills Section**: Add specific years of experience for each skill
2. **Work Experience**: Quantify achievements with metrics
3. **Summary**: Add a professional summary at the top

Overall, the resume shows good potential but needs more specific details.
"""


# ============================================================
# Your Service 3 Code (same as real implementation)
# ============================================================

class MockGeminiProvider:
    """
    Mock version of GeminiProvider for demo purposes.
    In production, this would call the real Gemini API.
    """
    
    async def generate(self, prompt: str) -> str:
        """Simulate API call with delay"""
        print("   ⏳ [Mock] Calling Gemini API...")
        await asyncio.sleep(1)  # Simulate network delay
        print("   ✅ [Mock] Response received")
        return MOCK_LLM_RESPONSE


class MockLLMService:
    """
    LLM Service layer that processes responses.
    This is the REAL logic - only the API call is mocked.
    """
    
    def __init__(self):
        self.provider = MockGeminiProvider()
    
    async def analyze_resume(self, prompt: str) -> dict:
        """
        Main method: Take prompt → Call LLM → Parse response
        """
        # Step 1: Call LLM (mocked)
        raw_response = await self.provider.generate(prompt)
        
        # Step 2: Parse response into structured data (REAL LOGIC)
        result = self._parse_analyze_response(raw_response)
        
        return result
    
    def _parse_analyze_response(self, raw_response: str) -> dict:
        """
        Parse raw LLM text into structured JSON.
        This is YOUR core logic - extracting useful data from AI response.
        """
        # In production, this would be more sophisticated
        # For demo, we show the structure
        return {
            "suggestions": [
                {
                    "section": "Skills",
                    "original": "Python, FastAPI",
                    "improved": "Python (3 years), FastAPI, REST API Design",
                    "reason": "Added years of experience"
                },
                {
                    "section": "Work Experience", 
                    "original": "Developed backend services",
                    "improved": "Developed backend services handling 10K+ requests/day",
                    "reason": "Added quantifiable metrics"
                }
            ],
            "overall_score": 72,
            "summary": "Resume shows potential, needs more specific details",
            "raw_llm_response": raw_response  # Keep original for debugging
        }


# ============================================================
# Demo Flow
# ============================================================

async def run_demo():
    print("\n" + "🎬 " * 15)
    print("  SERVICE 3 DEMO (Mock Version - No API Key Required)")
    print("🎬 " * 15)
    
    # ========================================
    # STEP 1: Receive prompt from upstream
    # ========================================
    print("\n" + "=" * 60)
    print("📍 STEP 1: Receive Prompt from Upstream")
    print("=" * 60)
    
    upstream_prompt = """
    Please analyze this resume:
    
    Name: John Doe
    Skills: Python, FastAPI, MySQL
    Experience: 3 years backend development
    
    Target Job: Senior Backend Engineer (requires 5 years)
    """
    
    print(f"\n📥 INPUT (what upstream gives you):")
    print("-" * 40)
    print(upstream_prompt)
    print("-" * 40)
    
    # ========================================
    # STEP 2: Your Service processes it
    # ========================================
    print("\n" + "=" * 60)
    print("📍 STEP 2: Your Service 3 Processes the Request")
    print("=" * 60)
    
    print("\n🔧 What happens inside:")
    print("   1. Receive prompt")
    print("   2. Send to Gemini API (mocked here)")
    print("   3. Parse raw response")
    print("   4. Return structured data")
    
    service = MockLLMService()
    result = await service.analyze_resume(upstream_prompt)
    
    # ========================================
    # STEP 3: Return structured response
    # ========================================
    print("\n" + "=" * 60)
    print("📍 STEP 3: Return Structured Response to Downstream")
    print("=" * 60)
    
    print(f"\n📤 OUTPUT (what you return to downstream/frontend):")
    print("-" * 40)
    
    # Pretty print without raw_llm_response for cleaner output
    output = {k: v for k, v in result.items() if k != "raw_llm_response"}
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("-" * 40)
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "=" * 60)
    print("✅ DEMO SUMMARY")
    print("=" * 60)
    print("""
    Your Service 3 Responsibilities:
    
    ┌─────────────────────────────────────────────────────────┐
    │  INPUT:   Prompt string from upstream                   │
    │           ↓                                             │
    │  PROCESS: 1. Send to Gemini API                         │
    │           2. Handle errors/retries                      │
    │           3. Parse raw text → structured JSON           │
    │           ↓                                             │
    │  OUTPUT:  Structured data for downstream/frontend       │
    └─────────────────────────────────────────────────────────┘
    
    Key Value You Provide:
    • Encapsulate LLM provider (Gemini/OpenAI/etc)
    • Error handling (timeout, rate limit, API failures)
    • Response parsing (text → JSON)
    """)


if __name__ == "__main__":
    asyncio.run(run_demo())
