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
 [6.1 Flow diagram of system release & deployments](#61-flow-diagram-of-system-release--deployments)  

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

* Backend \-\> FastAPI  
* Frontend \-\> React  
* AI integration \-\> LLM Provider or other API, instead of building NLP models  
* Infra \-\> Deploy on Google Cloud  
* CI/CD \-\> Automated deployment using GitHub Actions  
* Architecture \-\> Monolithic backend  
* Data Model \-\> session-based user data

## 2. System architecture

### 2.1 High level system architecture diagram

The system architecture follows a client–server model with a monolithic FastAPI backend, a React-based frontend, integration with an LLM provider for optimization, and Google Cloud components for hosting and temporary file storage. The architecture ensures stateless execution, simplified deployment, and scalability using Cloud Run.
<figure>
    <img src="./src/architecture.png"
         alt="high level architecture diagram" height="400">
    <figcaption>High Level Architecture Diagram</figcaption>
</figure>

### 2.2 Description on each component

#### 2.2.1 Frontend (React)

* Chat page  
* Add / Edit Job details  
* Chat input and message rendering  
* Converts user actions into API call
* Resume upload and download

#### 2.2.2 Backend (FastAPI Monolithic Service)

* Handles all business logic, routing, and API responses  
* Manages temporary resume/JD data for each session  
* Construct prompts using job \+ resume \+ chat history and send them to the LLM, then return responses  
* Returns structured JSON data containing optimized content and generated files, allowing the frontend to handle rendering.
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

<img src="./src/data1.png" alt="Data Flow 1" height="300">

Data flow 1: upload resume, save to GCS, create id, return session_id

<img src="./src/data2.png" alt="Data Flow 2" height="300">

Data flow 2: request from frontend, get resume from GCS at backend, request from backend, construct response from LLM, return response to frontend

Key Components:

* Request Router: Routes request to Mode A or Mode B based on JD presence  
* Resume Parser: Extracts resume content  
* JD Handler: Processes job description (Mode B only)  
* Match Scoring: Calculates resume-JD compatibility (Mode B only)  
* LLM Engine: Calls external LLM Provider for optimization  
* Export Service: Generates final document  
* Cloud Storage: Stores temporary files  
* Pre-signed URL: Enables secure download

### 3.2 How data is used for communication

1. Between Frontend and Backend  
   - Requests:  
	 - JSON for JD text, analysis requests, optimization requests  
	 - multipart/form-data for resume uploads  
  
   - Responses:  
     - JSON containing:  
       - Analysis results (scores, suggestions)  
       - Matching results (match score, gap analysis, JD-specific suggestions)  
       - Optimization results (download URL, file metadata)  
       - Session ID and status information

2. Between Backend and LLM Provider
   - JSON payload containing:  
	 - Extracted resume text
	 - JD text  
     - Prompt  
     - LLM API returns optimized resume text and suggested score  
3. Between Backend and Cloud Storage
   - Temporary file objects written and retrieved via URLs  
   - Files are never publicly accessible and scoped per session

## 4. Interface design

### 4.1 API Summary Table

| Method | Endpoint | Name | Request Body | Response |
| ----- | ----- | ----- | ----- | ----- |
| **POST** | `/api/resumes` | Upload Resume | File (multipart) | resume_id, parsed_data |
| **POST** | `/api/resumes/analyze` | Analyze Resume | focus_areas (optional) | scores, suggestions |
| **POST** | `/api/resumes/match` | Match with JD | job_description | match_score, gaps |
| **POST** | `/api/resumes/optimize` | Generate optimized file | JD (optional), format | file_url, content |

### 4.2 API Endpoints

#### 4.2.1 Upload & Parse Resume

Endpoint: `POST /api/resumes`

Description: Uploads and parses resume file, stores resume in GCS.

Request Body (multipart/form-data):
```
file: <resume_file>  // PDF, DOCX, DOC, TXT (max 5MB)
```
Response (201 Created):
```
{
	"status": "created",
	"code": 201,
	"data": {
		"sid": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
		"timestamp": "2024-01-15T10:30:00Z",
		"expireAt": "2024-01-16T10:30:00Z"
	}
}
```
Error Responses:

* `400 Bad Request`: Invalid file format or size  
* `500 Internal Server Error`: Server error

---

#### 4.2.2 Analyze Resume

Endpoint: `POST /api/resumes/analyze`

Description: Analyzes resume quality using AI, returns suggestions.

Request Body (JSON):
```
{
	sid: "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```
Response (200 OK):
```
{
 "status": "ok",
 "data": {
		"suggestions": [
			{
				"category": "content",
				"priority": "high",
				"title": "Add quantifiable metrics",
				"description": "Several achievements lack specific numbers...",
				"example": "Instead of 'Improved performance', write 'Improved performance by 40%'"
			},
			{  
				…  
			}
		]
 	},
 	"timestamp": "2024-01-15T10:35:00Z"
}
```
Error Responses:

* `401 Unauthorized`: Invalid/missing token  
* `404 Not Found`: Resume not found  
* `500 Internal Server Error`: Backend Server error

---

#### 4.2.3 Match Resume with Job Description

Endpoint: `POST /api/resumes/match`

Description: Matches resume against job description using Gemini AI, returns match score and gaps.

Request Body (JSON):
```
{
	"sid": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
	"job_description": "We are seeking a Senior Software Engineer...",  // Required, 50-10000 chars
	"job_title": "Senior Software Engineer",  // Optional
	"company_name": "Tech Corp"  // Optional
}
```
Response (200 OK):
```
{
	"code": 200,
	"status": "ok",
	"body": {
		"job_info": {
			"job_title": "Senior Software Engineer",
			"company_name": "Tech Corp"
		},
		"overall_match_score": 78,
		"match_breakdown": {
			"skills_match": 85,
			"experience_match": 75,
			"education_match": 90,
			"keywords_match": 70
		},
		"matched_skills": [
			{
				"skill": "Python",
				"relevance": "high",
				"found_in_resume": true,
				"required_in_jd": true
			},
			{
				"skill": "React",
				"relevance": "high",
				"found_in_resume": true,
				"required_in_jd": true
			}
		],
		"missing\_skills": [
			{
				"skill": "Kubernetes",
				"relevance": "high",
				"importance": "high",
				"recommendation": "Consider adding Kubernetes experience"
			}
		],
		"suggestions": [
			{
				"category": "skills",
				"priority": "high",
				"title": "Highlight microservices experience",
				"description": "Make microservices more prominent...",
				"specific\_action": "Add 'Designed microservices' as key achievement"
			}
		],
		"recommendation": {
			"should_apply": true,
			"confidence": "high",
			"summary": "You are a strong candidate with 78% match..."
		}
	},
	"timestamp": "2024-01-15T10:40:00Z"
}
```
Error Responses:

* `401 Unauthorized`: Invalid/missing token  
* `500 Internal Server Error`: Server error

---

#### 4.2.4 Optimize Resume

Endpoint: `POST /api/resumes/optimize`

Description: Generates AI-optimized resume using AI, creates PDF/DOCX file, stores in GCS.

Request body (JSON):
```
{
	"sid": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
	"job_description": "We are seeking...",  // Optional (for JD-specific optimization)
	"template": "modern"  // Optional: "modern" | "classic" | "minimal" | "creative"
}
```
Response (200 OK):
```
{
 "status": "success",
 "data": {
   "optimization_template": "modern",
   "changes_summary": [
		{
			"section": "skills",
			"description": "Rewrote to emphasize relevant keywords"
		},
		{
			"section": "experience",
			"description": "Added quantifiable metrics and keywords"
		}
	 ],
   "encoded_file": "JVBERi0xLjQKJ…"  (base64)
	},
 "timestamp": "2024-01-15T10:45:00Z"
}
```
Error Responses:

* `401 Unauthorized`: Invalid/missing token  
* `500 Internal Server Error`: File generation error  

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

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

## 5. UI design

### 5.1 Simple wireframe for frontend components

### 5.2 Description of workflow and interaction

#### Scenario A: Uploading a Resume

**User Action:** User uploads a resume file

**Flow:**

1. User clicks "Upload Resume" button and selects a file  
2. Frontend sends the file via `multipart/form-data` to `POST /api/resume/upload`  
3. Backend receives and parses the resume file  
4. Backend stores the original file in Google Cloud Storage  
5. Backend parses the resume file to extract relevant information for internal processing  
6. Backend returns an upload success response with session id and a expiry datetime
7. Frontend stores the session id for the current workflow and displays "Upload Successful"

**Data Stored:**

* Frontend: session id, expiry datetime  
* Google Cloud Storage: Original resume file

#### Scenario B: Analyzing Resume

**User Action:** User requests AI analysis of their resume

**Flow:**

1. User clicks "Analyze My Resume" button  
2. Frontend sends `POST /api/resume/analyze` with session id  
3. Backend retrieves parsed resume data from GCS using session id  
4. Backend constructs LLM prompt with resume content  
5. Backend calls External LLM API for analysis  
6. LLM returns revision suggestions  
7. Backend returns analysis results to Frontend  
8. Frontend displays suggestions to user

**User Can:**

* Re-analyze the same resume without re-uploading

#### Scenario C: Analyzing Resume with JD (Matching Score)

**User Action:** User inputs a job description to match against their resume

**Flow:**

1. User enters or pastes job description text  
2. User clicks "Match" button  
3. Frontend sends `POST /api/resume/match` with session id and JD text  
4. Backend retrieves parsed resume data from GCS using session ID  
5. Backend constructs LLM prompt with:  
   * Resume content  
   * Job description  
6. Backend calls External LLM API for detailed matching analysis  
7. LLM returns matching score and JD-specific revision suggestions  
8. Backend returns matching results to Frontend  
9. Frontend displays matching score, gap analysis, and suggestions
10. Frontend stores matching history in localStorage

**User Can:**

* Try different job descriptions with the same resume  
* View history of all JD matches  

#### Scenario D: Optimizing and Downloading Resume

**User Action:** User requests AI-optimized resume for download

**Flow:**

##### Option 1: General Optimization (No JD)

1. User clicks "Optimize & Download" button  
2. Frontend sends `POST /api/resume/optimize` with session ID (no JD)  
3. Backend retrieves resume from GCS and parse resume  
4. Backend constructs LLM prompt for general optimization  
5. Backend calls External LLM API for optimization  
6. LLM returns optimized resume content  
7. Backend generates PDF/DOCX file from optimized content  
8. Backend uploads file to Google Cloud Storage and returns download URL to Frontend (or backend returns encoded file to frontend)
9. Frontend displays download button  
10. User clicks download button and downloads the optimized resume file

##### Option 2: JD-Specific Optimization (With JD)

1. User selects a previously analyzed JD from history (or enters new JD)  
2. User clicks "Optimize for This Job & Download" button  
3. Frontend sends `POST /api/resume/optimize` with session ID and JD text 
4. Backend retrieves resume data from GCS 
5. Backend constructs LLM prompt with resume + JD for targeted optimization  
6. Backend calls External LLM API for JD-specific optimization  
7. LLM returns JD-optimized resume content  
8. Backend generates PDF/DOCX file from optimized content  
9. Backend uploads file to Google Cloud Storage and returns download URL to Frontend (or backend returns encoded file to frontend)
10. Frontend displays download button  
11. User clicks download button and downloads the optimized resume file

**Data Stored:**

* Google Cloud Storage: Optimized resume file (PDF)

**User Can:**

* Generate multiple optimized versions (general vs. JD-specific)  

## 6. Infrastructure design

### 6.1 Flow diagram of system release & deployments

### 6.2 Continuous Integration with Github Action for testing and linting

### 6.3 Continuous Deployment with GCP for build and deploy
