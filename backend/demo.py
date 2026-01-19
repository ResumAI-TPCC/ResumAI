"""
Gemini LLM Provider 演示脚本
用于在会议上展示 Gemini 集成的正确性
"""

import asyncio
import sys

sys.path.insert(0, ".")

from app.services.llm import get_llm_provider


async def demo():
    print("=" * 60)
    print("🚀 ResumAI - Gemini LLM Provider 演示")
    print("=" * 60)

    # 1. 获取 Provider
    print("\n📦 步骤 1: 获取 LLM Provider...")
    provider = get_llm_provider()
    print(f"   ✅ 成功获取 Provider: {provider.provider_name}")

    # 示例简历
    resume = """
姓名：张三
职位：软件工程师
工作年限：3年

技能：
- Python (熟练)
- JavaScript, React (熟练)
- SQL, PostgreSQL (熟悉)
- Docker, Git (熟悉)

工作经历：
1. ABC科技公司 - 后端开发工程师 (2022-至今)
   - 负责电商平台后端 API 开发
   - 使用 Django 框架，日均处理 10 万请求
   - 参与数据库优化，查询性能提升 40%

2. XYZ互联网公司 - 初级开发工程师 (2020-2022)
   - 参与公司内部管理系统开发
   - 编写自动化测试脚本

教育背景：
- 本科 - 计算机科学与技术 - XX大学 (2016-2020)
"""

    # 示例职位描述
    job_description = """
职位：高级 Python 后端工程师

职责：
- 负责 AI 产品后端架构设计和开发
- 使用 FastAPI 构建高性能 API 服务
- 与 AI/ML 团队协作，集成大语言模型

要求：
- 5年以上 Python 开发经验
- 精通 FastAPI 或 Django 框架
- 有 AI/LLM 项目经验优先
- 熟悉 Docker、Kubernetes
- 良好的沟通能力和团队协作精神
"""

    # 2. 测试匹配功能
    print("\n📊 步骤 2: 分析简历与职位匹配度...")
    print("   (正在调用 Gemini API，请稍候...)")

    match_result = await provider.match(resume, job_description)

    print(f"\n   🎯 匹配分数: {match_result.score * 100:.0f}%")
    print(f"\n   📝 详细分析:")
    print(f"   {match_result.explanation}")
    print(f"\n   💡 改进建议:")
    for i, suggestion in enumerate(match_result.suggestions, 1):
        print(f"      {i}. {suggestion}")

    # 3. 测试分析功能
    print("\n" + "=" * 60)
    print("📋 步骤 3: 生成简历优化建议...")
    print("   (正在调用 Gemini API，请稍候...)")

    analyze_result = await provider.analyze(resume, job_description)

    print(f"\n   📄 分析结果:")
    print("-" * 40)
    # 只显示前 500 字符，避免太长
    analysis_preview = analyze_result.content[:800]
    if len(analyze_result.content) > 800:
        analysis_preview += "\n   ... (更多内容省略)"
    print(f"   {analysis_preview}")

    # 显示 token 使用情况
    if analyze_result.usage:
        print(f"\n   📈 Token 使用统计:")
        print(f"      - 输入 tokens: {analyze_result.usage.get('prompt_tokens', 'N/A')}")
        print(
            f"      - 输出 tokens: {analyze_result.usage.get('completion_tokens', 'N/A')}"
        )
        print(f"      - 总计 tokens: {analyze_result.usage.get('total_tokens', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ 演示完成！Gemini LLM Provider 工作正常")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())

