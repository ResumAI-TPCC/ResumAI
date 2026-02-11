"""
Prompt Templates for LLM

This module contains all prompt templates used for resume analysis and optimization.
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


# RA-45: Optimize without JD
OPTIMIZE_NO_JD_PROMPT_TEMPLATE = """You are a professional resume writer and career consultant. Your task is to rewrite and optimize the following resume to make it more professional, impactful, and ATS-friendly.

## Original Resume Content:
{resume_content}

## Instructions:
Rewrite the entire resume in clean, professional Markdown format. Make the following improvements:
1. Strengthen action verbs and make language more impactful
2. Add quantifiable metrics where possible (estimate reasonable numbers if needed)
3. Improve formatting and structure for better readability
4. Ensure consistent tense and professional tone
5. Optimize keywords for ATS (Applicant Tracking Systems)
6. Keep all factual information (names, dates, companies) unchanged

## Output Format:
Return the optimized resume as clean Markdown text. Use proper Markdown headings (#, ##), bullet points (-), and bold (**) formatting. Do NOT wrap the output in a JSON object or code block - just return the raw Markdown content directly.

Example structure:
# [Full Name]
**Email:** ... | **Phone:** ... | **Location:** ...

## Professional Summary
...

## Work Experience
### [Job Title] | [Company] | [Date Range]
- Achievement 1
- Achievement 2

## Education
...

## Skills
...
"""


# RA-46: Optimize with JD
OPTIMIZE_WITH_JD_PROMPT_TEMPLATE = """You are a professional resume writer and career consultant. Your task is to rewrite and optimize the following resume to be highly targeted for the specific job description provided.

## Original Resume Content:
{resume_content}

## Target Job Description:
{job_description}

## Instructions:
Rewrite the entire resume in clean, professional Markdown format, specifically tailored for the target job. Make the following improvements:
1. Prioritize and highlight experiences most relevant to the job description
2. Mirror key terminology and skills mentioned in the job description
3. Strengthen action verbs and quantify achievements relevant to the role
4. Add a targeted professional summary that aligns with the job requirements
5. Reorder sections to emphasize the most relevant qualifications first
6. Optimize keywords for ATS matching with the job description
7. Keep all factual information (names, dates, companies) unchanged

## Output Format:
Return the optimized resume as clean Markdown text. Use proper Markdown headings (#, ##), bullet points (-), and bold (**) formatting. Do NOT wrap the output in a JSON object or code block - just return the raw Markdown content directly.

Example structure:
# [Full Name]
**Email:** ... | **Phone:** ... | **Location:** ...

## Professional Summary
[Targeted summary aligned with the job description]

## Work Experience
### [Job Title] | [Company] | [Date Range]
- Achievement relevant to target job
- Achievement with quantifiable metrics

## Education
...

## Skills
[Skills prioritized by relevance to job description]
"""

