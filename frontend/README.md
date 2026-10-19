# ResumAI Frontend

Single-page React app for uploading a resume, viewing analysis / match results, downloading the optimized resume, and running a mock interview.

## Tech Stack

- React 18
- Vite
- Tailwind CSS 3
- Jest + React Testing Library
- ESLint 9 (flat config)

## Getting Started

```bash
# Install dependencies from lockfile
npm ci

# Configure the backend URL (defaults to http://localhost:8000/api)
cp .env.example .env

# Start development server
npm run dev

# Build for production
npm run build

# Add a new package
npm install <package-name>
```

## Tests and Lint

Run both before committing; CI runs the same commands.

```bash
npm run lint
npm test
```

## Project Structure

```
src/
├── pages/ResumeAnalysisPage.jsx   # Page shell; owns all app state
├── components/                    # Sidebar, AnalysisOutput, ResumePreview, FileUpload, LoadingState
│   └── interview/                 # Mock interview UI
├── hooks/useMockInterview.js      # Mock interview state
├── utils/
│   ├── api.js                     # Upload + analyze/match/optimize (submit + poll job)
│   ├── interviewApi.js            # Mock interview API calls
│   └── storage.js                 # localStorage session persistence
├── config/env.js                  # Reads VITE_* environment variables
└── tests/                         # Jest tests
```
