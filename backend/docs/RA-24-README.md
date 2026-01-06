# RA-24: Resume Upload - Parse File

## 📋 Overview

This feature implements resume file parsing functionality that extracts structured information from uploaded PDF and DOCX files.

## 🚀 Implementation Details

### New Files Created

1. **`app/schemas/resume.py`** - Pydantic models for request/response
2. **`app/services/resume_parser.py`** - Core parsing service
3. **`tests/test_resume_parse.py`** - Comprehensive test suite

### API Endpoint

**POST** `/api/resume/parse`

#### Request Body

```json
{
  "file_id": "uuid-from-upload",
  "storage_path": "storage/resumes/uuid/filename.pdf"
}
```

#### Response

```json
{
  "file_id": "uuid-from-upload",
  "filename": "resume.pdf",
  "status": "success",
  "parsed_data": {
    "full_name": "John Doe",
    "contact_info": {
      "email": "john.doe@example.com",
      "phone": "+1-555-1234",
      "linkedin": "https://linkedin.com/in/johndoe",
      "location": null
    },
    "summary": "Experienced software engineer...",
    "skills": ["Python", "FastAPI", "Docker"],
    "education": [
      {
        "institution": "University Name",
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "graduation_year": "2020"
      }
    ],
    "work_experience": [
      {
        "company": "Tech Company",
        "position": "Software Engineer",
        "duration": "2020-2023",
        "description": "Developed web applications..."
      }
    ],
    "raw_text": "Full extracted text from resume..."
  }
}
```

## 🔧 Dependencies Added

- `pypdf` (>=5.1.0) - PDF parsing
- `python-docx` (>=1.1.2) - DOCX parsing

## 🧪 Testing

Run tests with:

```bash
cd backend
python -m pytest tests/test_resume_parse.py -v
```

### Test Coverage

- ✅ Missing file handling (404)
- ✅ Invalid format handling (400)
- ✅ PDF parsing success
- ✅ DOCX parsing success
- ✅ Schema validation

## 📝 Usage Example

### Step 1: Upload Resume (RA-23)

```bash
curl -X POST http://localhost:8000/api/resume/ \
  -F "file=@resume.pdf"
```

Response:
```json
{
  "file_id": "abc-123",
  "filename": "resume.pdf",
  "storage_path": "storage/resumes/abc-123/resume.pdf"
}
```

### Step 2: Parse Resume (RA-24)

```bash
curl -X POST http://localhost:8000/api/resume/parse \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "abc-123",
    "storage_path": "storage/resumes/abc-123/resume.pdf"
  }'
```

## 🎯 Features

### Extracted Information

- **Personal Info**: Name, email, phone, LinkedIn
- **Professional Summary**: Career objective/summary
- **Skills**: Technical and soft skills list
- **Education**: Degree, institution, field of study
- **Work Experience**: Company, position, duration, responsibilities
- **Raw Text**: Complete extracted text for further processing

### Supported Formats

- ✅ PDF (`.pdf`)
- ✅ DOCX (`.docx`)
- ❌ DOC (legacy format not supported)
- ❌ TXT (plain text not supported)

## 🔮 Future Enhancements

1. **LLM Integration**: Use AI for better extraction accuracy
2. **NLP Enhancement**: Add spaCy/NLTK for entity recognition
3. **Location Extraction**: Implement address parsing
4. **Date Parsing**: Extract and normalize dates
5. **Confidence Scores**: Add confidence levels for extracted data
6. **Multi-language Support**: Parse resumes in different languages

## 🔗 Integration with RA-23

This feature works in conjunction with RA-23 (file upload). The workflow is:

1. Frontend uploads file → RA-23 endpoint
2. RA-23 saves file locally and returns `file_id` + `storage_path`
3. Frontend calls RA-24 with received data
4. RA-24 parses file and returns structured data

## ⚠️ Known Limitations

- **Regex-based parsing**: Current implementation uses regex patterns which may not catch all variations
- **English only**: Best results with English language resumes
- **Format dependent**: Parsing accuracy depends on resume formatting
- **No OCR**: Scanned PDFs (images) are not supported

## 📚 Related Tickets

- **RA-23**: Resume Upload - Upload File to GCS (prerequisite)
- **RA-22**: [FE] Resume Upload - Upload Logics (frontend integration)
- **RA-25**: [BE] Resume Upload - Unit Tests (additional tests)
