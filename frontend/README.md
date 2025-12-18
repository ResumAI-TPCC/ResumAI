# ResumAI Frontend

Match Analysis page - React frontend with Tailwind CSS.

## Tech Stack

- React 18
- Vite
- Tailwind CSS

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # UI Components (Skeleton)
│   │   ├── Sidebar.jsx              # Left sidebar
│   │   ├── FileUpload.jsx           # File upload component
│   │   ├── MatchAnalysis.jsx        # Center analysis area
│   │   ├── ScoreCard.jsx            # JD Match Score card
│   │   ├── ScoringPrinciples.jsx    # Scoring principles list
│   │   ├── AnalysisReasoning.jsx    # Analysis reasoning
│   │   └── ResumePreview.jsx        # Right preview panel
│   ├── pages/
│   │   └── MatchAnalysisPage.jsx    # Main page (3-column layout)
│   └── utils/
│       ├── api.js                   # API calls
│       ├── storage.js               # Session management
│       └── filePreview.js           # File preview
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Components (TODO)

| Component | Description | Status |
|-----------|-------------|--------|
| Sidebar | Left sidebar with inputs | Placeholder |
| FileUpload | Resume upload | Placeholder |
| MatchAnalysis | Analysis container | Placeholder |
| ScoreCard | JD Match Score card | Placeholder |
| ScoringPrinciples | Scoring criteria | Placeholder |
| AnalysisReasoning | AI analysis results | Placeholder |
| ResumePreview | Right preview panel | Placeholder |

## Features (TODO)

- [ ] Resume upload (PDF, DOCX, TXT)
- [ ] Job description input
- [ ] Match score display
- [ ] Scoring principles
- [ ] Analysis reasoning
- [ ] Resume preview
- [ ] Download optimized resume

