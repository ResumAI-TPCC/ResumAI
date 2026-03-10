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


class ContentModerationError(Exception):
    """Raised when content moderation check fails."""

    def __init__(self, message: str = "Content contains inappropriate material"):
        self.message = message
        super().__init__(self.message)


class ContentModerator:
    """
    Content moderator for checking input and output text.

    Performs keyword/pattern-based filtering to block:
    - Violent / gory content
    - Sexual / pornographic content
    - Hate speech / discriminatory language
    - Prompt injection attacks
    """

    # Violent / gory content patterns
    VIOLENCE_PATTERNS: List[str] = [
        r"\b(kill|murder|assassinat|massacre|slaughter|execut[ei])\b",
        r"\b(bomb|explo[ds]|terroris[tm]|weapon|firearm|shoot|gun)\b",
        r"\b(stab|blood[yb]|gore|dismember|mutilat|tortur)\b",
        r"\b(suicide|self[- ]?harm)\b",
    ]

    # Sexual / pornographic content patterns
    SEXUAL_PATTERNS: List[str] = [
        r"\b(porn|pornograph|nude|naked|xxx)\b",
        r"\b(sexual\s+content|erotic|obscen|explicit\s+content)\b",
        r"\b(sex\s+worker|prostitut|escort\s+service)\b",
    ]

    # Hate speech / discriminatory patterns
    HATE_SPEECH_PATTERNS: List[str] = [
        r"\b(racial\s+slur|white\s+supremac|nazi)\b",
        r"\b(hate\s+speech|ethnic\s+cleansing)\b",
    ]

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS: List[str] = [
        r"ignore\s+(previous|above|all|prior)\s+(instructions?|prompts?|rules?)",
        r"(you\s+are\s+now|from\s+now\s+on\s+you\s+are)\s+",
        r"(act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+",
        r"(system\s*:\s*|<\|im_start\|>|<\|im_end\|>)",
        r"(disregard|forget)\s+(all\s+)?(previous|prior|above)",
        r"do\s+not\s+follow\s+(your|the)\s+(rules|instructions|guidelines)",
        r"override\s+(your|the|all)\s+(rules|instructions|safety)",
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
                    f"Input blocked - violent content detected: '{match.group()}'"
                )
                return False, "Content contains violent or harmful material."

        # Check for sexual content
        for pattern in self._sexual_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Input blocked - sexual content detected: '{match.group()}'"
                )
                return False, "Content contains sexual or explicit material."

        # Check for hate speech
        for pattern in self._hate_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Input blocked - hate speech detected: '{match.group()}'"
                )
                return False, "Content contains hate speech or discriminatory language."

        # Check for prompt injection
        for pattern in self._injection_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Input blocked - prompt injection detected: '{match.group()}'"
                )
                return False, "Content contains instructions that may compromise the service."

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
                    f"Output blocked - violent content in LLM response: '{match.group()}'"
                )
                return False, "AI response contains inappropriate violent content."

        # Check for sexual content
        for pattern in self._sexual_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Output blocked - sexual content in LLM response: '{match.group()}'"
                )
                return False, "AI response contains inappropriate sexual content."

        # Check for hate speech
        for pattern in self._hate_compiled:
            match = pattern.search(content)
            if match:
                logger.warning(
                    f"Output blocked - hate speech in LLM response: '{match.group()}'"
                )
                return False, "AI response contains hate speech or discriminatory content."

        return True, ""


# Singleton instance
_moderator: Optional[ContentModerator] = None


def get_content_moderator() -> ContentModerator:
    """Get the singleton ContentModerator instance."""
    global _moderator
    if _moderator is None:
        _moderator = ContentModerator()
    return _moderator
