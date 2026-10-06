"""
Unit Tests for Prompt Templates and PromptBuilder

Tests cover:
- ChatPromptTemplate rendering for each operation
- PromptBuilder.validate_job_description input-quality checks
- get_prompt_builder singleton behaviour
"""

import pytest

from app.services.prompt import PromptBuilder, get_prompt_builder
from app.services.prompt.templates import (
    ANALYZE_PROMPT,
    MATCH_PROMPT,
    OPTIMIZE_NO_JD_PROMPT,
    OPTIMIZE_WITH_JD_PROMPT,
)


# ---------------------------------------------------------------------------
# ChatPromptTemplate rendering
# ---------------------------------------------------------------------------

class TestAnalyzePromptTemplate:
    """Tests for ANALYZE_PROMPT ChatPromptTemplate rendering."""

    def _render(self, resume_content: str):
        return ANALYZE_PROMPT.format_messages(resume_content=resume_content)

    def test_returns_two_messages(self):
        messages = self._render("John Doe, Software Engineer")
        assert len(messages) == 2

    def test_system_message_contains_safety_instruction(self):
        messages = self._render("Sample resume")
        system_content = messages[0].content
        assert "Safety Rules" in system_content

    def test_system_message_contains_persona(self):
        messages = self._render("Sample resume")
        assert "resume consultant" in messages[0].content

    def test_human_message_contains_resume_content(self):
        resume = "Jane Smith\nPython Developer\nExperience: 5 years at Acme Corp"
        messages = self._render(resume)
        assert "Jane Smith" in messages[1].content
        assert "Python Developer" in messages[1].content

    def test_human_message_contains_field_descriptions(self):
        messages = self._render("Sample resume")
        human = messages[1].content
        assert "category" in human
        assert "priority" in human
        assert "description" in human
        assert "example" in human

    def test_human_message_contains_priority_levels(self):
        messages = self._render("Sample resume")
        human = messages[1].content
        assert "high" in human
        assert "medium" in human
        assert "low" in human

    def test_human_message_contains_category_options(self):
        messages = self._render("Sample resume")
        human = messages[1].content
        for category in ("content", "skills", "format", "language"):
            assert category in human

    def test_no_json_format_instruction(self):
        """with_structured_output owns format; template must not duplicate it."""
        messages = self._render("Sample resume")
        full_text = " ".join(m.content for m in messages)
        assert "Return your analysis EXCLUSIVELY in JSON" not in full_text
        assert "```json" not in full_text


class TestMatchPromptTemplate:
    """Tests for MATCH_PROMPT ChatPromptTemplate rendering."""

    def _render(self, resume_content: str, job_description: str):
        return MATCH_PROMPT.format_messages(
            resume_content=resume_content,
            job_description=job_description,
        )

    def test_returns_two_messages(self):
        messages = self._render("Resume text", "Job description text")
        assert len(messages) == 2

    def test_system_contains_hiring_manager_persona(self):
        messages = self._render("Resume", "JD")
        assert "hiring manager" in messages[0].content

    def test_human_contains_both_inputs(self):
        resume = "Alice, Data Scientist"
        jd = "Looking for a data scientist with Python skills"
        messages = self._render(resume, jd)
        human = messages[1].content
        assert "Alice" in human
        assert "Python skills" in human

    def test_human_contains_scoring_formula(self):
        messages = self._render("Resume", "JD")
        human = messages[1].content
        assert "0.35" in human
        assert "0.25" in human
        assert "0.15" in human

    def test_no_json_format_instruction(self):
        messages = self._render("Resume", "JD")
        full_text = " ".join(m.content for m in messages)
        assert "Return your analysis EXCLUSIVELY in JSON" not in full_text
        assert "```json" not in full_text


class TestOptimizeNoJdPromptTemplate:
    """Tests for OPTIMIZE_NO_JD_PROMPT ChatPromptTemplate rendering."""

    def _render(self, resume_content: str, template: str = "modern"):
        return OPTIMIZE_NO_JD_PROMPT.format_messages(
            resume_content=resume_content,
            template=template,
        )

    def test_returns_two_messages(self):
        assert len(self._render("Resume")) == 2

    def test_system_contains_resume_writer_persona(self):
        messages = self._render("Resume")
        assert "resume writer" in messages[0].content

    def test_human_contains_resume_content(self):
        resume = "Bob Brown, DevOps Engineer"
        messages = self._render(resume)
        assert "Bob Brown" in messages[1].content

    def test_human_contains_template_variable(self):
        messages = self._render("Resume", template="executive")
        assert "executive" in messages[1].content

    def test_human_contains_markdown_output_instruction(self):
        messages = self._render("Resume")
        human = messages[1].content
        assert "Markdown" in human

    def test_no_jd_section_in_human(self):
        messages = self._render("Resume")
        assert "Job Description" not in messages[1].content


class TestOptimizeWithJdPromptTemplate:
    """Tests for OPTIMIZE_WITH_JD_PROMPT ChatPromptTemplate rendering."""

    def _render(self, resume_content: str, job_description: str, template: str = "modern"):
        return OPTIMIZE_WITH_JD_PROMPT.format_messages(
            resume_content=resume_content,
            job_description=job_description,
            template=template,
        )

    def test_returns_two_messages(self):
        assert len(self._render("Resume", "JD")) == 2

    def test_human_contains_jd(self):
        jd = "Senior backend engineer role requiring Go and Kubernetes"
        messages = self._render("Resume", jd)
        assert "Kubernetes" in messages[1].content

    def test_human_contains_resume_and_jd_sections(self):
        messages = self._render("Resume content", "JD content")
        human = messages[1].content
        assert "Resume Content" in human
        assert "Job Description" in human


class TestSafetyInstructionPresence:
    """Safety instruction must appear in system messages of all templates."""

    def test_analyze_system_has_safety(self):
        msgs = ANALYZE_PROMPT.format_messages(resume_content="x")
        assert "Safety Rules" in msgs[0].content

    def test_match_system_has_safety(self):
        msgs = MATCH_PROMPT.format_messages(resume_content="x", job_description="y")
        assert "Safety Rules" in msgs[0].content

    def test_optimize_no_jd_system_has_safety(self):
        msgs = OPTIMIZE_NO_JD_PROMPT.format_messages(resume_content="x", template="modern")
        assert "Safety Rules" in msgs[0].content

    def test_optimize_with_jd_system_has_safety(self):
        msgs = OPTIMIZE_WITH_JD_PROMPT.format_messages(
            resume_content="x", job_description="y", template="modern"
        )
        assert "Safety Rules" in msgs[0].content


# ---------------------------------------------------------------------------
# PromptBuilder.validate_job_description
# ---------------------------------------------------------------------------

class TestValidateJobDescription:
    """Tests for PromptBuilder.validate_job_description."""

    def test_valid_jd_passes(self):
        PromptBuilder.validate_job_description(
            "Looking for a senior Python engineer with 5+ years of experience."
        )

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="too short"):
            PromptBuilder.validate_job_description("Short")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            PromptBuilder.validate_job_description("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            PromptBuilder.validate_job_description("     ")

    def test_numeric_gibberish_raises(self):
        with pytest.raises(ValueError, match="meaningful text"):
            PromptBuilder.validate_job_description("1234567890 12345678901234567890")

    def test_exact_min_length_with_sufficient_alpha(self):
        jd = "a" * 20
        PromptBuilder.validate_job_description(jd)

    def test_borderline_alpha_ratio_passes(self):
        # 30 alpha chars + 10 non-alpha → ratio 0.75 ≥ 0.3
        PromptBuilder.validate_job_description("a" * 30 + "1" * 10)


# ---------------------------------------------------------------------------
# get_prompt_builder singleton
# ---------------------------------------------------------------------------

class TestGetPromptBuilder:
    """Tests for get_prompt_builder factory function."""

    def setup_method(self):
        import app.services.prompt.builder as builder_module
        builder_module._prompt_builder = None

    def test_returns_instance(self):
        assert isinstance(get_prompt_builder(), PromptBuilder)

    def test_singleton(self):
        assert get_prompt_builder() is get_prompt_builder()
