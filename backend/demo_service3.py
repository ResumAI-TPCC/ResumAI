"""
Service 3 Demo: Take Prompt → Send to LLM → Handle Response

This script demonstrates the core functionality of Service 3:
1. Receive a prompt from upstream (simulated)
2. Send the prompt to Gemini LLM
3. Parse and return structured response
"""

import asyncio
import json
from app.services.llm import get_llm_provider, LLMService
from app.services.llm.schemas import AnalyzeResult


async def demo_basic_call():
    """
    Demo 1: Basic LLM Call
    Shows: prompt in → raw response out
    """
    print("=" * 60)
    print("📍 Demo 1: Basic LLM Call (GeminiProvider)")
    print("=" * 60)
    
    # Step 1: Receive prompt from upstream (simulated)
    upstream_prompt = """
    请分析以下简历内容，给出改进建议：
    
    姓名：张三
    职位：Python 后端工程师
    技能：Python, FastAPI, MySQL
    经验：3年互联网开发经验
    
    请用 JSON 格式返回，包含 suggestions 数组。
    """
    
    print(f"\n📥 Input (from upstream):")
    print(f"   Prompt: {upstream_prompt[:50]}...")
    
    # Step 2: Send to Gemini
    print(f"\n🚀 Sending to Gemini API...")
    provider = get_llm_provider()
    
    try:
        raw_response = await provider.send_prompt(upstream_prompt)
        
        # Step 3: Return response
        print(f"\n📤 Output (raw response from Gemini):")
        print("-" * 40)
        print(raw_response)
        print("-" * 40)
        
        return raw_response
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


async def demo_with_parsing():
    """
    Demo 2: LLM Call with Response Parsing
    Shows: prompt in → structured JSON out
    """
    print("\n" + "=" * 60)
    print("📍 Demo 2: LLM Call with Parsing (LLMService)")
    print("=" * 60)
    
    # Step 1: Receive prompt from upstream
    upstream_prompt = """
    分析这份简历：
    - 姓名：李四
    - 技能：Java, Spring Boot
    - 经验：2年
    
    目标职位：高级后端工程师（要求5年经验）
    """
    
    print(f"\n📥 Input (from upstream):")
    print(f"   Prompt: {upstream_prompt[:50]}...")
    
    # Step 2: Use LLMService (includes parsing)
    print(f"\n🚀 Processing with LLMService...")
    service = LLMService()
    
    try:
        result = await service.analyze_resume(upstream_prompt)
        
        # Step 3: Return structured response
        print(f"\n📤 Output (structured response for downstream):")
        print("-" * 40)
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        print("-" * 40)
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


async def demo_error_handling():
    """
    Demo 3: Error Handling
    Shows: how Service 3 handles failures
    """
    print("\n" + "=" * 60)
    print("📍 Demo 3: Error Handling")
    print("=" * 60)
    
    provider = get_llm_provider()
    
    # Test with empty prompt
    print("\n🧪 Testing with empty prompt...")
    try:
        result = await provider.send_prompt("")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ✅ Caught error: {type(e).__name__}: {e}")


async def main():
    """Run all demos"""
    print("\n" + "🎬 " * 20)
    print("   SERVICE 3 DEMO: Take Prompt → Send to LLM → Handle Response")
    print("🎬 " * 20)
    
    # Check if API key is configured
    from app.core.config import settings
    if not settings.gemini_api_key:
        print("\n⚠️  Warning: GEMINI_API_KEY not set!")
        print("   Please add it to backend/.env file:")
        print("   GEMINI_API_KEY=your_api_key_here")
        print("\n   Get your key at: https://aistudio.google.com/app/apikey")
        return
    
    print(f"\n✅ API Key configured: {settings.gemini_api_key[:10]}...")
    print(f"✅ Model: {settings.gemini_model}")
    
    # Run demos
    await demo_basic_call()
    await demo_with_parsing()
    await demo_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
