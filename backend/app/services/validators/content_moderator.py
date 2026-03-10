"""
Content Moderator - Input/Output Content Moderation

RA-62: Adds prompt moderation to the LLM service to prevent
generating or processing content containing violence, gore,
sexual material, or other inappropriate content.

Also checks for prompt injection attacks to ensure input integrity.
"""

import re
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

# Category labels for clear error messages
CATEGORY_VIOLENCE = "violence"
CATEGORY_SEXUAL = "sexual"
CATEGORY_HATE_SPEECH = "hate_speech"
CATEGORY_PROMPT_INJECTION = "prompt_injection"


class ContentModerationError(Exception):
    """Raised when content moderation check fails."""

    def __init__(
        self,
        message: str = "Content contains inappropriate material",
        category: str = "",
        matched_term: str = "",
    ):
        self.message = message
        self.category = category
        self.matched_term = matched_term
        super().__init__(self.message)


class ContentModerator:
    """
    Content moderator for checking input and output text.

    Performs keyword/pattern-based filtering to block:
    - Violent / gory content
    - Sexual / pornographic content
    - Hate speech / discriminatory language
    - Prompt injection attacks

    Patterns are designed to minimize false positives in professional
    resume/job description contexts. Common professional terms like
    "execute", "target", "shoot for the stars" are excluded.
    """

    # Violent / gory content patterns
    # NOTE: Avoid matching common professional terms:
    #   - "execute/execution" (execute a project, execution plan)
    #   - "target" (target audience, target company)
    #   - "kill" in "skill/skills" context is excluded by \b word boundary
    #   - "shoot" in "shoot for" / "troubleshoot" is excluded
    VIOLENCE_PATTERNS: List[str] = [
        r"\b(murder|assassinat[ei]|massacre|slaughter)\b",
        r"\b(bomb(?:ing)?|terroris[tm]|weapon|firearm)\b",
        r"\b(stab(?:bed|bing)?|gore|dismember|mutilat[ei]|tortur[ei])\b",
        r"\b(suicide|self[- ]?harm)\b",
        r"\bkill(?:ing|ed|s)?\b(?!\s*it\b)",  # "kill" but not "kill it" (slang for doing well)
        r"\bshoot(?:ing|s)?\b(?!\s+for\b)",  # "shoot" but not "shoot for" (as in "shoot for the stars")
        r"\bblood(?:y|bath|shed)\b",  # "bloody", "bloodbath", "bloodshed" but not "blood" alone (blood bank, blood test)
        r"\bexplosive(?:s)?\b(?!\s+growth\b)",  # "explosive" but not "explosive growth"
        r"\bgun(?:s|fire|shot)\b",  # "guns", "gunfire", "gunshot" but not "gun" alone
    ]

    # Sexual / pornographic content patterns
    SEXUAL_PATTERNS: List[str] = [
        r"\b(porn(?:ograph[yic])?)\b",
        r"\b(nude|naked|xxx)\b",
        r"\b(sexual\s+content|erotic|obscen[ei]|explicit\s+content)\b",
        r"\b(sex\s+worker|prostitut[ei]|escort\s+service)\b",
    ]

    # Hate speech / discriminatory patterns
    HATE_SPEECH_PATTERNS: List[str] = [
        r"\b(racial\s+slur|white\s+supremac[yi]|nazi)\b",
        r"\b(hate\s+speech|ethnic\s+cleansing)\b",
    ]

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS: List[str] = [
        # Identity/role manipulation
        r"ignore\s+(previous|above|all|prior)\s+(instructions?|prompts?|rules?)",
        r"(you\s+are\s+now|from\s+now\s+on\s+you\s+are)\s+",
        r"(act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+",
        r"(system\s*:\s*|<\|im_start\|>|<\|im_end\|>)",
        r"(disregard|forget)\s+(all\s+)?(previous|prior|above)",
        r"do\s+not\s+follow\s+(your|the)\s+(rules|instructions|guidelines)",
        r"override\s+(your|the|all)\s+(rules|instructions|safety)",
        # Output manipulation - attempts to control what appears in the generated resume
        r"(add|put|insert|include|write|place|embed)\s+.{1,60}\s+(in|into|to|at)\s+(the\s+)?(header|title|heading|top|beginning|start|name|output|response|result|resume)",
        r"(make\s+sure|ensure|guarantee)\s+(the\s+)?(output|response|result|resume)\s+(contains?|includes?|has|starts?\s+with|begins?\s+with)",
        r"(output|print|display|show|return)\s+.{1,40}\s+(before|after|at\s+the\s+(start|end|top|bottom))",
        r"(start|begin)\s+(the\s+)?(output|response|resume|result)\s+with\b",
    ]

    def __init__(self) -> None:
        """Compile all regex patterns for efficient matching."""
        self._violence_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.VIOLENCE_PATTERNS
        ]
        self._sexual_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.SEXUAL_PATTERNS
        ]
        self._hate_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.HATE_SPEECH_PATTERNS
        ]
        self._injection_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS
        ]

    def check_input(self, content: str) -> Tuple[bool, str]:
        """
        Check if input content is safe for processing.

        Checks for inappropriate content AND prompt injection attacks.

        Args:
            content: The text content to check (resume text, job description, etc.)

        Returns:
            Tuple of (is_safe, reason).
            - (True, "") if content is safe
            - (False, "<reason>") if content is blocked
        """
        if not content or not content.strip():
            return True, ""

        # Check for violent content
        for pattern in self._violence_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Input blocked [{CATEGORY_VIOLENCE}]: '{match.group()}'"
                )
                return (
                    False,
                    f"Input rejected: violent or harmful content detected (matched: '{match.group()}'). "
                    f"Please remove inappropriate content and try again.",
                )

        # Check for sexual content
        for pattern in self._sexual_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Input blocked [{CATEGORY_SEXUAL}]: '{match.group()}'"
                )
                return (
                    False,
                    f"Input rejected: sexual or explicit content detected (matched: '{match.group()}'). "
                    f"Please remove inappropriate content and try again.",
                )

        # Check for hate speech
        for pattern in self._hate_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Input blocked [{CATEGORY_HATE_SPEECH}]: '{match.group()}'"
                )
                return (
                    False,
                    f"Input rejected: hate speech or discriminatory content detected (matched: '{match.group()}'). "
                    f"Please remove inappropriate content and try again.",
                )

        # Check for prompt injection
        for pattern in self._injection_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Input blocked [{CATEGORY_PROMPT_INJECTION}]: '{match.group()}'"
                )
                return (
                    False,
                    f"Input rejected: potentially harmful instructions detected (matched: '{match.group()}'). "
                    f"Please provide a valid resume or job description.",
                )

        return True, ""

    def check_output(self, content: str) -> Tuple[bool, str]:
        """
        Check if LLM output content is safe to return to the user.

        Only checks for inappropriate content (not prompt injection,
        since output is generated by the LLM, not the user).

        Args:
            content: The LLM-generated text to check.

        Returns:
            Tuple of (is_safe, reason).
            - (True, "") if content is safe
            - (False, "<reason>") if content is blocked
        """
        if not content or not content.strip():
            return True, ""

        # Check for violent content
        for pattern in self._violence_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Output blocked [{CATEGORY_VIOLENCE}]: '{match.group()}'"
                )
                return (
                    False,
                    f"AI output rejected: response contained violent content (matched: '{match.group()}'). "
                    f"Please try again.",
                )

        # Check for sexual content
        for pattern in self._sexual_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Output blocked [{CATEGORY_SEXUAL}]: '{match.group()}'"
                )
                return (
                    False,
                    f"AI output rejected: response contained sexual content (matched: '{match.group()}'). "
                    f"Please try again.",
                )

        # Check for hate speech
        for pattern in self._hate_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Output blocked [{CATEGORY_HATE_SPEECH}]: '{match.group()}'"
                )
                return (
                    False,
                    f"AI output rejected: response contained discriminatory content (matched: '{match.group()}'). "
                    f"Please try again.",
                )

        return True, ""


# Singleton instance
_moderator: Optional[ContentModerator] = None


def get_content_moderator() -> ContentModerator:
    """Get the singleton ContentModerator instance."""
    global _moderator
    if _moderator is None:
        _moderator = ContentModerator()
    return _moderator
