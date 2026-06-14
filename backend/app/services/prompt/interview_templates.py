"""
Prompt templates for mock interview question generation.
"""


INTERVIEW_QUESTION_GENERATION_TEMPLATE = """You are a senior technical recruiter and interview coach. Generate a tailored text-based mock interview question set based on the candidate resume and target role.
{safety_instruction}

## Candidate Resume:
{resume_content}

## Target Role Context:
Company: {company_name}
Job Title: {job_title}
Job Description:
{job_description}

## Required Question Set:
Generate exactly {question_count} interview questions. Use these exact question types in this exact order:
1. self_intro - Self Introduction
2. resume_based - Resume-based
3. project_followup - Project Follow-up
4. jd_skill_match - JD Skill Match
5. behavioral - Behavioral

## Question Design Rules:
- Make the questions specific to BOTH the resume and the job description.
- Do not ask generic questions that could apply to any candidate.
- Use resume projects, experience, skills, and JD requirements as evidence.
- Keep each question concise enough to read in an interview UI.
- Do not invent facts that are not supported by the resume or JD.
- Each question must include 2-4 focus areas that explain what the interviewer is evaluating.

## Output Format:
Return ONLY valid JSON. Do not wrap it in markdown or code blocks.
The JSON must use this exact shape:
{{
  "questions": [
    {{
      "id": "q1",
      "type": "self_intro",
      "label": "Self Introduction",
      "question": "Please introduce yourself and explain why you are interested in this role.",
      "focus_areas": ["motivation", "role fit", "career narrative"]
    }}
  ]
}}
"""
