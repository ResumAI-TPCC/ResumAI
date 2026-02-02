from app.services.prompt import get_prompt_builder

resume_content = """
John Doe
Software Engineer | San Francisco, CA

Experience:
- Built web applications using React
- Improved system performance by 40%
- Led a team of 5 engineers

Skills: Python, React, AWS
"""

builder = get_prompt_builder()
prompt = builder.build_analyze_prompt(resume_content)

print(prompt)