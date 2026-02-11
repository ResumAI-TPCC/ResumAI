"""
Prompt Templates for LLM
Strictly aligned with Resume Schemas and Design Doc 4.2
"""

# --- Analyze Resume Template ---
ANALYZE_PROMPT_TEMPLATE = """You are a professional resume consultant. Analyze the following resume and provide actionable improvement suggestions.

## Resume Content:
{resume_content}

## Instructions:
Analyze the resume thoroughly. Focus on:
1. Content quality and relevance
2. Use of action verbs and quantifiable achievements
3. Skills presentation and keywords
4. Overall structure and formatting
5. Language clarity and professionalism

## Output Format:
Return your analysis EXCLUSIVELY in JSON format with a "suggestions" array.
Each suggestion MUST include these exact fields:
- category: One of ["content", "skills", "format", "language"]
- priority: One of ["high", "medium", "low"]
- title: A brief title (max 10 words)
- description: A detailed explanation of why this matters
- example: A specific "Before vs After" example

Example JSON Structure:
```json
{{
  "suggestions": [
    {{
      "category": "content",
      "priority": "high",
      "title": "Add quantifiable metrics",
      "description": "Several achievements lack specific numbers. Recruiter value data-driven results.",
      "example": "Instead of 'Improved performance', write 'Improved performance by 40%'"
    }}
  ]
}}
```
"""

# --- Match Resume Template ---
MATCH_PROMPT_TEMPLATE = """You are a hiring manager. Match the following resume against the job description (JD).

## Resume Content:
{resume_content}

## Job Description:
{job_description}

## Instructions:
1. Calculate a match score (0-100).
2. Breakdown the score into 4 categories: skills, experience, education, and keywords.
3. Provide specific suggestions to improve the match.

## Output Format:
Return your analysis EXCLUSIVELY in JSON format with the following structure:
- match_score: Integer (0-100)
- match_breakdown:
    - skills_match: Integer (0-100)
    - experience_match: Integer (0-100)
    - education_match: Integer (0-100)
    - keywords_match: Integer (0-100)
- suggestions: An array of objects, each containing:
    - category: String
    - priority: "high", "medium", or "low"
    - title: String
    - description: String
    - action: String (A specific action to take on the resume)

Example JSON Structure:
```json
{{
  "match_score": 75,
  "match_breakdown": {{
    "skills_match": 80,
    "experience_match": 70,
    "education_match": 90,
    "keywords_match": 60
  }},
  "suggestions": [
    {{
      "category": "skills",
      "priority": "high",
      "title": "Highlight React experience",
      "description": "The JD requires 3+ years of React.",
      "action": "Move React projects to the top of your experience section"
    }}
  ]
}}
```
"""

# --- Optimize Resume Template ---
OPTIMIZE_PROMPT_TEMPLATE = """You are a resume writing expert. Rewrite the following resume to make it more professional and better aligned with the provided job description (if any).

## Resume Content:
{resume_content}

## Job Description (Optional):
{job_description}

## Style/Template:
{template}

## Instructions:
1. Improve the wording using strong action verbs.
2. Fix any grammatical or structural issues.
3. Optimize for ATS (Applicant Tracking Systems).
4. Return the FULL improved resume content in professional Markdown format.

## Output Format:
Return the FULL optimized resume in Markdown.
"""
