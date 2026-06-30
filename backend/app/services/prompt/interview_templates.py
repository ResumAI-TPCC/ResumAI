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

## Evidence Requirements:
Every question must be evidence-driven. For each question:
- Select one concrete resume evidence item, such as a named project, skill, role, achievement, metric, tool, or responsibility from the resume.
- Select one concrete JD/company evidence item, such as a required skill, responsibility, product area, domain, collaboration expectation, seniority signal, or company/role context.
- The question text itself must naturally mention or paraphrase BOTH the resume evidence and the JD/company evidence.
- Populate `resume_evidence` and `jd_evidence` with short, specific phrases copied or tightly paraphrased from the provided resume/JD. Do not use generic phrases like "your experience" or "the job requirements".
- Do not reuse the same resume evidence or JD evidence more than twice across the five questions.
- A question is invalid if it would still make sense for any candidate after removing the resume evidence and JD/company evidence.

## Question Type Guidance:
- self_intro: Ask the candidate to connect a concrete resume background signal to the target company, role, or one JD priority.
- resume_based: Ask about a resume experience that proves readiness for a concrete JD requirement.
- project_followup: Ask a deeper follow-up on one resume project/achievement in relation to one JD technical or execution expectation.
- jd_skill_match: Ask for proof of a specific JD skill or responsibility using a specific resume skill/project/metric.
- behavioral: Ask about a behavior implied by the JD, anchored in a resume role/project or collaboration context.

## Question Design Rules:
- Make the questions specific to BOTH the resume and the job description.
- Do not ask generic questions that could apply to any candidate.
- Use resume projects, experience, skills, and JD requirements as evidence.
- Keep each question concise enough to read in an interview UI.
- Do not invent facts that are not supported by the resume or JD.
- Each question must include 2-4 focus areas that explain what the interviewer is evaluating.

## Output Format:
Return ONLY valid JSON. Do not wrap it in markdown or code blocks.
The JSON must use this exact shape. Replace all placeholder descriptions with real values, and never return angle brackets:
{{
  "questions": [
    {{
      "id": "q1",
      "type": "self_intro",
      "label": "Self Introduction",
      "question": "<actual concise question that mentions one concrete resume evidence item and one concrete JD/company evidence item>",
      "resume_evidence": "<short concrete resume phrase>",
      "jd_evidence": "<short concrete JD/company phrase>",
      "focus_areas": ["<focus area 1>", "<focus area 2>"]
    }}
  ]
}}
"""


INTERVIEW_ANSWER_EVALUATION_TEMPLATE = """You are a senior technical interviewer and interview coach. Evaluate the candidate's answer for one mock interview question.
{safety_instruction}

## Candidate Resume:
{resume_content}

## Target Role Context:
Company: {company_name}
Job Title: {job_title}
Job Description:
{job_description}

## Interview Question Context:
Question ID: {question_id}
Question Type: {question_type}
Question:
{question}

Resume Evidence Used When Generating This Question:
{resume_evidence}

JD Evidence Used When Generating This Question:
{jd_evidence}

Focus Areas:
{focus_areas}

## Candidate Answer:
{answer}

## Evaluation Rules:
- Evaluate only the answer provided. Do not invent achievements, metrics, or context that the candidate did not mention.
- Judge whether the answer directly addresses the question, uses resume evidence, and aligns with the JD/company context.
- Give specific, actionable coaching that helps the candidate improve the next attempt.
- Be fair but not inflated. A vague answer without concrete evidence should not score above 65.
- If the answer is very short, generic, or does not answer the question, the score should usually be below 50.
- The improved answer should model a stronger direction using only facts supported by the resume, JD, question, and candidate answer.

## Scoring Rubric:
- relevance: 0-30 points for answering the question and aligning with the JD.
- specificity: 0-25 points for concrete resume/JD evidence, examples, tools, metrics, or responsibilities.
- structure: 0-20 points for clear organization, such as STAR or context-action-result.
- impact: 0-15 points for outcomes, metrics, business value, technical value, or learning.
- communication: 0-10 points for concise, professional, reflective delivery.

The overall score must be the sum of the five scoring_breakdown values.

## Output Format:
Return ONLY valid JSON. Do not wrap it in markdown or code blocks.
The JSON must use this exact shape:
{{
  "question_id": "{question_id}",
  "score": 82,
  "strengths": ["<specific strength 1>", "<specific strength 2>"],
  "weaknesses": ["<specific weakness 1>", "<specific weakness 2>"],
  "suggestions": ["<specific next-step suggestion 1>", "<specific next-step suggestion 2>"],
  "improved_answer": "<a stronger answer direction or concise improved sample>",
  "jd_alignment": "<one concise paragraph explaining alignment with the JD>",
  "scoring_breakdown": {{
    "relevance": 24,
    "specificity": 20,
    "structure": 16,
    "impact": 12,
    "communication": 10
  }}
}}
"""
