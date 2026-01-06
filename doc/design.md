# ResumAI System Design Document

**Version: MVP Draft**  
**Author: Asheng, Bowen, Harrison, Hugo, Lin, Jason, Jayking, Jerome, Jimmy, John, Max, Ron**  
**Date: 2025.12**

[**1. Introduction and overview**](#1-introduction-and-overview)  

[**2. System architecture**](#2-system-architecture)  
 [2.1 High level system architecture diagram](#21-high-level-system-architecture-diagram)  
 [2.2 Description on each component](#22-description-on-each-component)  
  [2.2.1 Frontend (React)](#221-frontend-react)  
  [2.2.2 Backend (FastAPI Monolithic Service)](#222-backend-fastapi-monolithic-service)  
  [2.2.3 LLM Provider API](#223-llm-provider-api)  
  [2.2.4 Google Cloud Storage (GCS) — Resume File Storage](#224-google-cloud-storage-gcs---resume-file-storage)  
  [2.2.5 Google Cloud Run](#225-google-cloud-run)  
 [2.3 Explanation on design decisions and trade-offs](#23-explanation-on-design-decisions-and-trade-offs)  
  [2.3.1 Monolithic vs. Microservices](#231-monolithic-vs-microservices)  
  [2.3.2 Use External LLM Instead of Custom NLP](#232-use-external-llm-instead-of-custom-nlp)  
  [2.3.3 Cloud Run vs. Compute Engine](#233-cloud-run-vs-compute-engine)  
  [2.3.4 Session-Based Data Instead of User Accounts](#234-session-based-data-instead-of-user-accounts)  

[**3. Data design**](#3-data-design)  
 [3.1 Data flow diagram and description](#31-data-flow-diagram-and-description)  
  [Scenario A: Uploading a Resume](#scenario-a-uploading-a-resume)  
  [Scenario B: Analyzing Resume](#scenario-b-analyzing-resume)  
  [Scenario C: Analyzing Resume with JD (Matching Score)](#scenario-c-analyzing-resume-with-jd-matching-score)  
  [Scenario D: Optimizing and Downloading Resume](#scenario-d-optimizing-and-downloading-resume)  
   [Option 1: General Optimization (No JD)](#option-1-general-optimization-no-jd)  
   [Option 2: JD-Specific Optimization (With JD)](#option-2-jd-specific-optimization-with-jd)  
 [3.2 How data is used for communication](#32-how-data-is-used-for-communication)  

[**4. Interface design**](#4-interface-design)  
 [4.1 API Summary Table](#41-api-summary-table)  
 [4.2 API Endpoints](#42-api-endpoints)  
  [4.2.1 Upload & Parse Resume](#421-upload--parse-resume)  
  [4.2.2 Analyze Resume](#422-analyze-resume)  
  [4.2.3 Match Resume with Job Description](#423-match-resume-with-job-description)  
  [4.2.4 Optimize Resume](#424-optimize-resume)  
 [4.3 HTTP Status Codes](#43-http-status-codes)  

[**5. UI design**](#5-ui-design)  
 [5.1 Simple wireframe for frontend components](#51-simple-wireframe-for-frontend-components)  
 [5.2 Description of workflow and interaction](#52-description-of-workflow-and-interaction)  

[**6. Infrastructure design**](#6-infrastructure-design)  
 [6.1 Development Workflow](#61-development-workflow)  
 [6.2 Continuous Integration with GitHub Actions](#62-continuous-integration-with-github-actions)  
 [6.3 Continuous Deployment with GCP](#63-continuous-deployment-with-gcp)

## 1. Introduction and overview

ResumAI is a web-based AI resume optimization platform designed to help users transform their resumes into job-aligned, professional documents. By analyzing both the user's uploaded resume and a target job description (JD), the system generates an improved version of the resume along with match score and suggestions.

At the MVP stage, ResumAI supports the following user-facing functions:

* Uploading resumes in PDF, DOCX, TXT, or plain text format  
* Inputting JD text  
* AI-powered resume optimization using an external LLM provider  
* Calculating resume–JD match score  
* Exporting the optimized resume in Markdown format, facilitating easy version control and content editing.

The product workflow remains intentionally simple to support fast user interaction:

**1. Upload Resume → AI Analyzation → Revision Suggestions**

**2. Upload Resume → Input JD → AI Analyzation → View Matching Score & Revision Suggestions**

**3. Upload Resume → Input JD (Optional) → AI Optimization → Download Improved Resume**

The technical stack include:

* Backend -> FastAPI  
* Frontend -> React  
* AI integration -> LLM Provider or other API, instead of building NLP models  
* Infra -> Deploy on Google Cloud  
* CI/CD -> Automated deployment using GitHub Actions  
* Architecture -> Monolithic backend  
* Data Model -> session-based user data

## 2. System architecture

### 2.1 High level system architecture diagram

The system architecture follows a client–server model with a monolithic FastAPI backend, a React-based frontend, integration with an LLM provider for optimization, and Google Cloud components for hosting and temporary file storage. The architecture ensures stateless execution, simplified deployment, and scalability using Cloud Run.

<img src="./src/architecture.png" alt="high level architecture diagram" height="400">

### 2.2 Description on each component

#### 2.2.1 Frontend (React)

* Chat page  
* Add / Edit Job modals  
* Chat input and message rendering  
* Converts user actions into API call
* Resume upload and download

#### 2.2.2 Backend (FastAPI Monolithic Service)

* Handles all business logic, routing, and API responses  
* Manages temporary resume/JD data for each session  
* Construct prompts using job + resume + chat history and send them to the LLM, then return responses  
* Returns structured JSON data containing optimized content, allowing the frontend to handle rendering and file generation.  
* Store and retrieve resume files from Google Cloud Storage  
* Ensures file-level privacy for each session

#### 2.2.3 LLM Provider API

* Performs resume rewriting and optimization  
* Generates suggestions and improved text  
* Provides semantic comparison for match scoring  
* **External API** (e.g., OpenAI, Anthropic, Gemini)

#### 2.2.4 Google Cloud Storage (GCS) — Resume File Storage

* Stores uploaded files temporarily

#### 2.2.5 Google Cloud Run

* Automatic scaling  
* No server maintenance  
* Pay-per-use efficiency  
* Ideal for stateless API workloads

### 2.3 Explanation on design decisions and trade-offs

#### 2.3.1 Monolithic vs. Microservices

Choice: Monolithic FastAPI server  
Reason: The MVP includes only three major functional areas:

* Resume  
* Job Cards  
* Chat

Splitting them into separate microservices would add unnecessary overhead and slow down development.

A monolithic backend keeps deployment simple and development fast.

#### 2.3.2 Use External LLM Instead of Custom NLP

Choice: External LLM Provider API  
Reason: No need to train ML models; faster time-to-market  
Trade-off: Dependency on external provider, cost per request

#### 2.3.3 Cloud Run vs. Compute Engine

Choice: Google Cloud Run  
Reason: 

* Fully managed auto-scaling  
* No server/VM maintenance  
* Much lower cost for low-traffic MVP projects  
* Extremely fast deployment and rollback  
* Naturally fits a stateless FastAPI application  
  Compute Engine would be heavy, costly, and unnecessary—"Using a large  cast-iron wok just to fry two eggs."

Trade-off: Limited control over long-running processes (not required for MVP)

#### 2.3.4 Session-Based Data Instead of User Accounts

Choice: Anonymous usage with session tokens  
Reason: MVP does not include login; privacy preserved through scoped sessions  
Trade-off: No long-term data persistence until Phase 2

## 3. Data design
### 3.1 Data flow diagram and description

<img src="./src/data1.png" alt="data flow diagram 1" height="400">

<img src="./src/data2.png" alt="data flow diagram 2" height="400">

Data flow1: upload resume, save to GCS, create id, return session_id

Data flow2: request from frontend, get resume from GCS at backend, request from backend, construct response from LLM, return response to frontend

Key Components:

* Request Router: Routes request to Mode A or Mode B based on JD presence
* Resume Parser: Extracts resume content
* JD Handler: Processes job description (Mode B only)
* Match Scoring: Calculates resume-JD compatibility (Mode B only)
* LLM Engine: Calls external LLM Provider for optimization
* Export Service: Generates final document
* Cloud Storage: Stores temporary files

### 3.2 How data is used for communication

1. Between Frontend and Backend  
   - Requests:  
	 - JSON for JD text, analysis requests, optimization requests  
	 - multipart/form-data for resume uploads  
  
   - Responses:
     - JSON containing:
       - Analysis results (suggestions)
       - Matching results (match score, suggestions)
       - Optimization results (encoded_file)
       - Session ID and status information

2. Between Backend and LLM Provider
   - JSON payload containing:  
	 - Extracted resume text
	 - JD text  
     - Prompt  
     - LLM API returns optimized resume text  
3. Between Backend and Cloud Storage
   - Temporary file objects written and retrieved via URLs  
   - Files are never publicly accessible and scoped per session

## 4. Interface design

### 4.1 API Summary Table

| Method | Endpoint | Name | Request Body | Response |
| ----- | ----- | ----- | ----- | ----- |
| **POST** | `/api/resumes` | Upload Resume | File (multipart) | session_id, expire_at |
| **POST** | `/api/resumes/analyze` | Analyze Resume | session_id | suggestions |
| **POST** | `/api/resumes/match` | Match with JD | session_id, job_description | match_score, suggestions |
| **POST** | `/api/resumes/optimize` | Generate optimized file | session_id, JD (optional) | encoded_file |

### 4.2 API Endpoints

#### 4.2.1 Upload & Parse Resume

Endpoint: `POST /api/resumes`

Description: Uploads and parses resume file, stores resume in GCS.

Request Body (multipart/form-data):
```
file: <resume_file>  // PDF, DOCX, DOC, TXT (max 5MB)
```

Response (201 Created):
```json
{
  "code": 201,
  "status": "ok",
  "data": {
    "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "expire_at": "2024-01-15T11:30:00Z"
  }
}
```

Error Responses:
* `400 Bad Request`: Invalid file format or size
* `500 Internal Server Error`: Server error

---

#### 4.2.2 Analyze Resume

Endpoint: `POST /api/resumes/analyze`

Description: Analyzes resume quality using Gemini AI, returns suggestions.

Request Body (JSON):
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

Response (200 OK):
```json
{
  "code": 200,
  "status": "ok",
  "data": {
    "suggestions": [
      {
        "category": "content",
        "priority": "high",
        "title": "Add quantifiable metrics",
        "description": "Several achievements lack specific numbers...",
        "example": "Instead of 'Improved performance', write 'Improved performance by 40%'"
      }
    ]
  }
}
```

Error Responses:
* `400 Bad Request`: Invalid request
* `404 Not Found`: Resume not found
* `500 Internal Server Error`: Server error

---

#### 4.2.3 Match Resume with Job Description

Endpoint: `POST /api/resumes/match`

Description: Matches resume against job description using Gemini AI, returns match score and suggestions.

Request Body (JSON):
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "job_description": "We are seeking a Senior Software Engineer...",
  "job_title": "Senior Software Engineer",
  "company_name": "Tech Corp"
}
```

Response (200 OK):
```json
{
  "code": 200,
  "status": "ok",
  "data": {
    "match_score": 78,
    "match_breakdown": {
      "skills_match": 85,
      "experience_match": 75,
      "education_match": 90,
      "keywords_match": 70
    },
    "suggestions": [
      {
        "category": "skills",
        "priority": "high",
        "title": "Highlight microservices experience",
        "description": "Make microservices more prominent...",
        "action": "Add 'Designed microservices' as key achievement"
      }
    ]
  }
}
```

Error Responses:
* `400 Bad Request`: Missing/invalid job description
* `404 Not Found`: Resume not found
* `500 Internal Server Error`: Server error

---

#### 4.2.4 Optimize Resume

Endpoint: `POST /api/resumes/optimize`

Description: Generates AI-optimized resume using Gemini AI, returns encoded file.

Request Body (JSON):
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "job_description": "We are seeking...",
  "template": "modern"
}
```

Response (200 OK):
```json
{
  "code": 200,
  "status": "ok",
  "data": {
    "encoded_file": "JVBERi0xLjQKJ..."
  }
}
```

Error Responses:
* `400 Bad Request`: Invalid parameters
* `404 Not Found`: Resume not found
* `500 Internal Server Error`: Server error

### 4.3 HTTP Status Codes

| Code | Status | Usage |
| ----- | ----- | ----- |
| **200** | OK | Successful request |
| **201** | Created | Resource created (upload) |
| **400** | Bad Request | Invalid input |
| **401** | Unauthorized | Auth required/invalid |
| **404** | Not Found | Resource not found |
| **422** | Unprocessable Entity | Cannot process file/data |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server error |
| **502** | Bad Gateway | External service error |
| **503** | Service Unavailable | Service down |

## 5. UI design

### 5.1 Simple wireframe for frontend components

The frontend consists of a single-page application with the following layout:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Header / Logo                           │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                  │
│   Sidebar    │              Main Content Area                   │
│              │                                                  │
│  ┌────────┐  │  ┌────────────────────────────────────────────┐  │
│  │Upload  │  │  │                                            │  │
│  │Resume  │  │  │         Resume Preview Panel               │  │
│  └────────┘  │  │                                            │  │
│              │  │  - Displays uploaded resume content        │  │
│  ┌────────┐  │  │  - Shows parsing status                    │  │
│  │Enter   │  │  │                                            │  │
│  │JD      │  │  └────────────────────────────────────────────┘  │
│  └────────┘  │                                                  │
│              │  ┌────────────────────────────────────────────┐  │
│  ┌────────┐  │  │                                            │  │
│  │Analyze │  │  │         Analysis Output Panel              │  │
│  └────────┘  │  │                                            │  │
│              │  │  - Match score (if JD provided)            │  │
│  ┌────────┐  │  │  - AI suggestions list                     │  │
│  │Optimize│  │  │  - Download optimized resume button        │  │
│  └────────┘  │  │                                            │  │
│              │  └────────────────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────────────────┘
```

**Components:**

| Component | Description |
| --------- | ----------- |
| **Sidebar** | Navigation and action buttons (Upload, Enter JD, Analyze, Optimize) |
| **FileUpload** | Drag-and-drop or click to upload resume (PDF, DOCX, TXT) |
| **ResumePreview** | Displays the content of uploaded resume |
| **AnalysisOutput** | Shows AI analysis results, match score, and suggestions |

### 5.2 Description of workflow and interaction

#### Scenario A: Uploading a Resume

**User Action:** User uploads a resume file

**Flow:**

1. User clicks "Upload Resume" button and selects a file
2. Frontend sends the file via `multipart/form-data` to `POST /api/resumes`
3. Backend receives and parses the resume file
4. Backend stores the original file in Google Cloud Storage
5. Backend returns session_id and expire_at
6. Frontend stores session_id and expire_at in localStorage and displays "Upload Successful"

**Data Stored:**

* Google Cloud Storage: Original resume file
* Frontend localStorage: session_id, expire_at

#### Scenario B: Analyzing Resume

**User Action:** User requests AI analysis of their resume

**Flow:**

1. User clicks "Analyze My Resume" button
2. Frontend sends `POST /api/resumes/analyze` with session_id
3. Backend retrieves resume file from Google Cloud Storage using session_id
4. Backend constructs LLM prompt with resume content
5. Backend calls External LLM API for analysis
6. LLM returns revision suggestions
7. Backend returns suggestions to Frontend
8. Frontend displays suggestions to user

**User Can:**

* Re-analyze the same resume without re-uploading

#### Scenario C: Analyzing Resume with JD (Matching Score)

**User Action:** User inputs a job description to match against their resume

**Flow:**

1. User enters or pastes job description text
2. User clicks "Analyze Match" button
3. Frontend sends `POST /api/resumes/match` with session_id and JD text
4. Backend retrieves resume file from Google Cloud Storage using session_id
5. Backend parses the job description
6. Backend calls External LLM API for matching analysis
7. LLM returns match score and suggestions
8. Backend returns match results to Frontend
9. Frontend displays match score and suggestions to user

**User Can:**

* Try different job descriptions with the same resume

#### Scenario D: Optimizing and Downloading Resume

**User Action:** User requests AI-optimized resume for download

**Flow:**

##### Option 1: General Optimization (No JD)

1. User clicks "Optimize & Download" button
2. Frontend sends `POST /api/resumes/optimize` with session_id (no JD)
3. Backend retrieves resume file from Google Cloud Storage
4. Backend calls External LLM API for optimization
5. LLM returns optimized resume content
6. Backend generates file and encodes as base64
7. Backend returns encoded_file to Frontend
8. Frontend decodes the file and triggers download

##### Option 2: JD-Specific Optimization (With JD)

1. User enters job description text
2. User clicks "Optimize for This Job & Download" button
3. Frontend sends `POST /api/resumes/optimize` with session_id and JD text
4. Backend retrieves resume file from Google Cloud Storage
5. Backend calls External LLM API for JD-specific optimization
6. LLM returns optimized resume content
7. Backend generates file and encodes as base64
8. Backend returns encoded_file to Frontend
9. Frontend decodes the file and triggers download

**User Can:**

* Generate optimized versions (general or JD-specific)

## 6. Infrastructure design

### 6.1 Development Workflow

1. Team lead creates tasks in Jira and assigns to developers
2. Developer creates a feature branch from `develop` (e.g., `feat/RA-19`)
3. Developer implements the feature and pushes to their branch
4. Developer creates a Pull Request to `develop` branch
5. Code owner reviews the PR
6. After approval, PR is merged to `develop`
7. When ready for production release, `develop` is merged to `main`

### 6.2 Continuous Integration with GitHub Actions

GitHub Actions automates testing and linting on every pull request to ensure code quality before merging.

* Triggered by: Pull requests to `develop` branch
* Actions: Run unit tests, integration tests, and linting checks
* Result: PR is blocked if tests fail; code owner review is required

### 6.3 Continuous Deployment with GCP

Google Cloud Platform handles build and deployment automation when changes are merged.

* `develop` branch: Deploys to staging/development environment
* `main` branch: Deploys to production environment
* Build: Docker image is built and pushed to Google Container Registry
* Deploy: Cloud Run automatically deploys the new image
