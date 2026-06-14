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
