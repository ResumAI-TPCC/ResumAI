"""
Prompt Templates for LLM

This module contains all prompt templates used for resume analysis.
Templates use Python string formatting with named placeholders.
"""

ANALYZE_PROMPT_TEMPLATE = """You are a professional resume consultant with expertise in career development and hiring practices. Please analyze the following resume and provide actionable improvement suggestions.

## Resume Content:
{resume_content}

## Instructions:
Analyze the resume thoroughly and provide specific, actionable suggestions for improvement.

Please return your analysis in JSON format with a "suggestions" array. Each suggestion should include:
- category: The category of the suggestion ("content", "skills", "format", "language")
- priority: The priority level ("high", "medium", "low")
- title: A brief title for the suggestion
- description: A detailed description of the issue and why it matters
- example: A specific example of how to implement the improvement

Return format:
```json
{{
  "suggestions": [
    {{
      "category": "content",
      "priority": "high",
      "title": "Add quantifiable metrics",
      "description": "Several achievements lack specific numbers. Quantifiable results make your accomplishments more credible and impactful to recruiters.",
      "example": "Instead of 'Improved system performance', write 'Improved system performance by 40%, reducing page load time from 5s to 3s'"
    }}
  ]
}}
```

Focus on:
1. Content quality and relevance
2. Use of action verbs and quantifiable achievements
3. Skills presentation and keywords
4. Overall structure and formatting
5. Language clarity and professionalism
"""

