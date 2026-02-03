"""
Unit Tests for PromptBuilder

Tests the prompt generation functionality for resume analysis.
"""

import pytest

from app.services.prompt import PromptBuilder, get_prompt_builder



class TestPromptBuilder:
    """Test suite for PromptBuilder class."""

    def setup_method(self):
        """Reset singleton before each test."""
        global _prompt_builder
        import app.services.prompt.builder as builder_module
        builder_module._prompt_builder = None

    def test_build_analyze_prompt_basic(self):
        """Test basic analyze prompt generation with valid content."""
        builder = PromptBuilder()
        resume_content = """John Doe
Software Engineer
Experience:
- Built web applications using React and Node.js
- Collaborated with cross-functional teams
"""
        prompt = builder.build_analyze_prompt(resume_content)

        # Verify resume content is included in prompt
        assert "John Doe" in prompt
        assert "Software Engineer" in prompt
        assert "React and Node.js" in prompt

        # Verify prompt structure elements
        assert "Resume Content:" in prompt
        assert "JSON" in prompt
        assert "suggestions" in prompt

    def test_build_analyze_prompt_strips_whitespace(self):
        """Test that resume content is properly stripped of leading/trailing whitespace."""
        builder = PromptBuilder()
        resume_content = "   \n\nJohn Doe\nEngineer\n\n   "

        prompt = builder.build_analyze_prompt(resume_content)

        # Content should be stripped
        assert "John Doe\nEngineer" in prompt

    def test_build_analyze_prompt_empty_string_raises(self):
        """Test that empty string raises ValueError."""
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="resume_content cannot be empty"):
            builder.build_analyze_prompt("")

    def test_build_analyze_prompt_whitespace_only_raises(self):
        """Test that whitespace-only string raises ValueError."""
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="resume_content cannot be empty"):
            builder.build_analyze_prompt("   \n\t  ")

    def test_build_analyze_prompt_none_raises(self):
        """Test that None input raises ValueError."""
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="resume_content cannot be empty"):
            builder.build_analyze_prompt(None)

    def test_build_analyze_prompt_contains_required_instructions(self):
        """Test that prompt contains all required instruction elements."""
        builder = PromptBuilder()
        resume_content = "Sample Resume Content"

        prompt = builder.build_analyze_prompt(resume_content)

        # Check for category options
        assert "content" in prompt
        assert "skills" in prompt
        assert "format" in prompt
        assert "language" in prompt

        # Check for priority options
        assert "high" in prompt
        assert "medium" in prompt
        assert "low" in prompt

        # Check for required fields
        assert "category" in prompt
        assert "priority" in prompt
        assert "title" in prompt
        assert "description" in prompt
        assert "example" in prompt


class TestGetPromptBuilder:
    """Test suite for get_prompt_builder factory function."""

    def setup_method(self):
        """Reset singleton before each test."""
        import app.services.prompt.builder as builder_module
        builder_module._prompt_builder = None

    def test_get_prompt_builder_returns_instance(self):
        """Test that get_prompt_builder returns a PromptBuilder instance."""
        builder = get_prompt_builder()

        assert isinstance(builder, PromptBuilder)

    def test_get_prompt_builder_singleton(self):
        """Test that get_prompt_builder returns the same instance."""
        builder1 = get_prompt_builder()
        builder2 = get_prompt_builder()

        assert builder1 is builder2

    def test_get_prompt_builder_functional(self):
        """Test that the singleton instance works correctly."""
        builder = get_prompt_builder()
        resume_content = "Test Resume"

        prompt = builder.build_analyze_prompt(resume_content)

        assert "Test Resume" in prompt

