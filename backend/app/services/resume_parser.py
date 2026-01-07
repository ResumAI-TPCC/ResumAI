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
            # Log full error internally, return generic message to client
            print(f"PDF parsing error: {str(e)}")
            raise ValueError("Failed to parse PDF file")

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
            # Log full error internally, return generic message to client
            print(f"DOCX parsing error: {str(e)}")
            raise ValueError("Failed to parse DOCX file")

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

        # Extract phone number with validation
        phone_pattern = r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}\b"
        raw_phones = re.findall(phone_pattern, raw_text)
        # Filter to valid phone numbers (7-15 digits)
        phones = [p for p in raw_phones if 7 <= len(re.sub(r"\D", "", p)) <= 15]
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
        skills_pattern = r"(?:skills?|technical skills?|core competencies)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|employment|work history|education|$)"
        match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)

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

            # Intelligent field classification
            current_entry = []
            for line in lines:
                current_entry.append(line)
                if len(current_entry) >= 3:
                    education_list.append(ResumeParserService._classify_education_fields(current_entry))
                    current_entry = []
            
            # Process remaining partial entry
            if current_entry:
                education_list.append(ResumeParserService._classify_education_fields(current_entry))

        return education_list[:5]  # Limit to 5 entries
    
    @staticmethod
    def _classify_education_fields(entry_lines: list[str]) -> Education:
        """Classify education entry fields by content patterns"""
        institution = None
        degree = None
        field = None
        
        for line in entry_lines:
            lower_line = line.lower()
            if institution is None and re.search(r"\b(university|college|institute|school)\b", lower_line):
                institution = line
            elif degree is None and re.search(r"\b(bachelor|master|ph\.?d|phd|b\.?sc|m\.?sc|ba|bs|beng|meng|mba)\b", lower_line):
                degree = line
            elif field is None:
                field = line
        
        # Fallback to positional mapping if classification failed
        if institution is None and len(entry_lines) > 0:
            institution = entry_lines[0]
        if degree is None and len(entry_lines) > 1:
            degree = entry_lines[1]
        if field is None and len(entry_lines) > 2:
            field = entry_lines[2]
        
        return Education(institution=institution, degree=degree, field=field)

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
        summary_pattern = r"(?:summary|objective|profile|about)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|employment|work history|education|skills|$)"
        match = re.search(summary_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            summary = match.group(1).strip()
            # Limit length
            return summary[:500] if len(summary) > 500 else summary

        return None


class MemoryResumeParser:
    """Adapter for parsing resume from memory (file content)"""
    
    @staticmethod
    async def parse_file(file_content: bytes, filename: str, file_type: str) -> ResumeData:
        """
        Parse resume from memory buffer
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            file_type: MIME type
            
        Returns:
            ResumeData: Extracted resume information
        """
        import tempfile
        from pathlib import Path
        
        # Security: Extract only the basename to prevent path traversal
        # This removes any directory components from the filename
        safe_filename = Path(filename).name
        
        # Validate filename doesn't contain path traversal patterns
        if ".." in safe_filename or safe_filename.startswith(("/", "\\")):
            raise ValueError("Invalid filename")
        
        # Determine file extension from safe filename
        if safe_filename.endswith('.pdf'):
            suffix = '.pdf'
        elif safe_filename.endswith('.docx'):
            suffix = '.docx'
        elif safe_filename.endswith('.txt'):
            suffix = '.txt'
        else:
            raise ValueError(f"Unsupported file format: {safe_filename}")
        
        # For PDF/DOCX, we need to use temporary file
        if suffix in ['.pdf', '.docx']:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(file_content)
                tmp.flush()
                tmp_path = Path(tmp.name)
            
            try:
                return ResumeParserService.parse_file(tmp_path, safe_filename)
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            # For text files, parse directly
            raw_text = file_content.decode('utf-8', errors='ignore')
            return ResumeParserService._extract_structured_data(raw_text, safe_filename)


def get_resume_parser():
    """Factory function to get resume parser instance"""
    return MemoryResumeParser()
