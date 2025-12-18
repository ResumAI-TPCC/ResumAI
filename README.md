# ResumAI

AI-powered resume optimization platform that transforms your resume into a job-aligned professional document.

## Project Structure

```
ResumAI/
├── frontend/                    # React Frontend (Vite + Tailwind CSS)
│   ├── src/
│   │   ├── components/          # UI Components (Skeleton)
│   │   │   ├── Sidebar.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   ├── MatchAnalysis.jsx
│   │   │   ├── ScoreCard.jsx
│   │   │   ├── ScoringPrinciples.jsx
│   │   │   ├── AnalysisReasoning.jsx
│   │   │   └── ResumePreview.jsx
│   │   ├── pages/
│   │   │   └── MatchAnalysisPage.jsx
│   │   └── utils/
│   │       ├── api.js
│   │       ├── storage.js
│   │       └── filePreview.js
│   └── package.json
│
├── backend/                     # Express Backend
│   ├── server.js
│   └── package.json
│
└── .github/workflows/           # CI/CD
    └── ci.yml
```

## Tech Stack

### Frontend
- React 18
- Vite
- Tailwind CSS

### Backend
- Node.js
- Express
- Multer (file upload)

## Getting Started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
npm install
npm run start
```

## Features (TODO)

- 📄 Resume upload (PDF, DOCX, TXT)
- 💼 Job description matching
- 🤖 AI-powered analysis
- 📊 Match score & gap analysis
- 📝 Resume optimization
- ⬇️ Download optimized resume

## Current Status

**Skeleton Version** - Component placeholders are set up, implementation pending.
