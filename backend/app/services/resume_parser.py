"""
Resume Parser Service
RA-24: Parse PDF and DOCX resume files and extract structured data
"""

import re
from pathlib import Path
from typing import Optional

from docx import Document
from pypdf import PdfReader

from app.schemas.resume import ContactInfo, Education, ResumeData, WorkExperience


class ResumeParserService:
    """Service for parsing resume files (PDF/DOCX) and extracting information"""

    @staticmethod
    def parse_file(file_path: Path, filename: str) -> ResumeData:
        """
        Parse resume file and extract structured data

        Args:
            file_path: Path to the resume file
            filename: Original filename

        Returns:
            ResumeData: Structured resume information

        Raises:
            ValueError: If file format is not supported
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            raw_text = ResumeParserService._extract_text_from_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            raw_text = ResumeParserService._extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        # Extract structured data from raw text
        return ResumeParserService._extract_structured_data(raw_text, filename)

    @staticmethod
    def _extract_text_from_pdf(file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(file_path)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    @staticmethod
    def _extract_text_from_docx(file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text_parts = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {str(e)}")

    @staticmethod
    def _extract_structured_data(raw_text: str, filename: str) -> ResumeData:
        """
        Extract structured information from raw text using regex patterns

        Note: This is a basic implementation. For production, consider using:
        - NLP libraries (spaCy, NLTK)
        - LLM-based extraction
        - Specialized resume parsing services
        """
        # Extract email
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, raw_text)
        email = emails[0] if emails else None

        # Extract phone number (simplified pattern)
        phone_pattern = r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}"
        phones = re.findall(phone_pattern, raw_text)
        phone = phones[0] if phones else None

        # Extract LinkedIn URL
        linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+"
        linkedin_urls = re.findall(linkedin_pattern, raw_text, re.IGNORECASE)
        linkedin = linkedin_urls[0] if linkedin_urls else None

        # Extract name (first non-empty line, often the name)
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        full_name = lines[0] if lines else None

        # Extract skills (keywords after "Skills" section)
        skills = ResumeParserService._extract_skills(raw_text)

        # Extract education
        education = ResumeParserService._extract_education(raw_text)

        # Extract work experience
        work_experience = ResumeParserService._extract_work_experience(raw_text)

        # Extract summary
        summary = ResumeParserService._extract_summary(raw_text)

        contact_info = ContactInfo(
            email=email,
            phone=phone,
            linkedin=linkedin,
            location=None,  # TODO: Implement location extraction
        )

        return ResumeData(
            full_name=full_name,
            contact_info=contact_info,
            summary=summary,
            skills=skills,
            education=education,
            work_experience=work_experience,
            raw_text=raw_text,
        )

    @staticmethod
    def _extract_skills(text: str) -> list[str]:
        """Extract skills from resume text"""
        skills = []

        # Look for skills section
        skills_pattern = r"(?:skills?|technical skills?|core competencies)[\s:]*([^\n]+(?:\n(?!\n)[^\n]+)*)"
        match = re.search(skills_pattern, text, re.IGNORECASE)

        if match:
            skills_text = match.group(1)
            # Split by common separators
            skill_items = re.split(r"[,;•·\|]|\n", skills_text)
            skills = [s.strip() for s in skill_items if s.strip() and len(s.strip()) > 2]

        # Limit to first 20 skills
        return skills[:20]

    @staticmethod
    def _extract_education(text: str) -> list[Education]:
        """Extract education information"""
        education_list = []

        # Look for education section
        edu_pattern = r"(?:education|academic background)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|skills|$)"
        match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            edu_text = match.group(1)
            lines = [line.strip() for line in edu_text.split("\n") if line.strip()]

            # Simple heuristic: every 2-4 lines form one education entry
            current_entry = []
            for line in lines:
                current_entry.append(line)
                if len(current_entry) >= 3:
                    education_list.append(
                        Education(
                            institution=current_entry[0] if len(current_entry) > 0 else None,
                            degree=current_entry[1] if len(current_entry) > 1 else None,
                            field=current_entry[2] if len(current_entry) > 2 else None,
                        )
                    )
                    current_entry = []

        return education_list[:5]  # Limit to 5 entries

    @staticmethod
    def _extract_work_experience(text: str) -> list[WorkExperience]:
        """Extract work experience information"""
        experience_list = []

        # Look for experience section
        exp_pattern = r"(?:experience|employment|work history)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|education|skills|$)"
        match = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            exp_text = match.group(1)
            lines = [line.strip() for line in exp_text.split("\n") if line.strip()]

            # Simple heuristic: company, position, duration pattern
            current_entry = []
            for line in lines:
                current_entry.append(line)
                if len(current_entry) >= 3:
                    experience_list.append(
                        WorkExperience(
                            company=current_entry[0] if len(current_entry) > 0 else None,
                            position=current_entry[1] if len(current_entry) > 1 else None,
                            duration=current_entry[2] if len(current_entry) > 2 else None,
                        )
                    )
                    current_entry = []

        return experience_list[:10]  # Limit to 10 entries

    @staticmethod
    def _extract_summary(text: str) -> Optional[str]:
        """Extract professional summary"""
        # Look for summary/objective section
        summary_pattern = r"(?:summary|objective|profile|about)[\s:]*\n([^\n]+(?:\n(?!\n)[^\n]+)*)"
        match = re.search(summary_pattern, text, re.IGNORECASE)

        if match:
            summary = match.group(1).strip()
            # Limit length
            return summary[:500] if len(summary) > 500 else summary

        return None
