"""
Tests for mock interview prompt generation.
"""

import pytest

from app.services.prompt.interview_builder import InterviewPromptBuilder


def test_build_question_generation_prompt_contains_context():
    builder = InterviewPromptBuilder()

    prompt = builder.build_question_generation_prompt(
        resume_content="Jane Doe\nBackend Engineer\nBuilt FastAPI services.",
        job_description="We need a Python engineer with API experience.",
        job_title="Software Engineer",
        company_name="Tech Corp",
    )

    assert "Jane Doe" in prompt
    assert "Python engineer" in prompt
    assert "Software Engineer" in prompt
    assert "Tech Corp" in prompt
    assert "self_intro" in prompt
    assert "resume_based" in prompt
    assert "project_followup" in prompt
    assert "jd_skill_match" in prompt
    assert "behavioral" in prompt
    assert '"questions"' in prompt
    assert "resume_evidence" in prompt
    assert "jd_evidence" in prompt
    assert "Every question must be evidence-driven" in prompt
    assert "The question text itself must naturally mention" in prompt


def test_build_question_generation_prompt_rejects_empty_resume():
    builder = InterviewPromptBuilder()

    with pytest.raises(ValueError, match="resume_content cannot be empty"):
        builder.build_question_generation_prompt(
            resume_content="",
            job_description="Valid job description",
        )


def test_build_question_generation_prompt_rejects_empty_jd():
    builder = InterviewPromptBuilder()

    with pytest.raises(ValueError, match="job_description cannot be empty"):
        builder.build_question_generation_prompt(
            resume_content="Valid resume",
            job_description="",
        )


def test_build_answer_evaluation_prompt_contains_context():
    builder = InterviewPromptBuilder()

    prompt = builder.build_answer_evaluation_prompt(
        resume_content="Jane Doe\nBuilt FastAPI services.",
        job_description="We need a Python engineer with API experience.",
        job_title="Software Engineer",
        company_name="Tech Corp",
        question_id="q2",
        question_type="resume_based",
        question="Which FastAPI service proves your API experience?",
        resume_evidence="Built FastAPI services",
        jd_evidence="Python engineer with API experience",
        focus_areas=["resume relevance", "ownership"],
        answer="I built FastAPI services for analytics workflows.",
    )

    assert "Candidate Answer" in prompt
    assert "I built FastAPI services" in prompt
    assert "Which FastAPI service" in prompt
    assert "Python engineer" in prompt
    assert "resume relevance" in prompt
    assert "Scoring Rubric" in prompt
    assert "scoring_breakdown" in prompt
    assert "improved_answer" in prompt
    assert "jd_alignment" in prompt


def test_build_answer_evaluation_prompt_rejects_empty_answer():
    builder = InterviewPromptBuilder()

    with pytest.raises(ValueError, match="answer cannot be empty"):
        builder.build_answer_evaluation_prompt(
            resume_content="Valid resume",
            job_description="Valid JD",
            question_id="q1",
            question_type="self_intro",
            question="Tell me about yourself.",
            answer="",
        )
