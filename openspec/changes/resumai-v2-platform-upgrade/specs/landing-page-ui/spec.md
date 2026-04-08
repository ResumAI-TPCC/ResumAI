## ADDED Requirements

### Requirement: Marketing landing page
The system SHALL serve a marketing landing page at `/` for unauthenticated visitors that communicates value and drives sign-up.

#### Scenario: Landing page renders for unauthenticated users
- **WHEN** an unauthenticated user visits `/`
- **THEN** the landing page renders with a hero section, feature highlights (analyze, match, optimize), and a "Sign in with Google" CTA

#### Scenario: Authenticated user is redirected from landing page
- **WHEN** an authenticated user visits `/`
- **THEN** they are redirected to `/dashboard`

### Requirement: Redesigned analysis dashboard
The system SHALL present a redesigned dashboard at `/dashboard` that replaces the current single-page layout with a structured multi-panel design.

#### Scenario: Upload + result panels are distinct
- **WHEN** the user loads the dashboard
- **THEN** a sidebar shows resume history; the main panel shows upload or active job status; a results panel shows the latest analysis output

#### Scenario: Responsive layout on mobile
- **WHEN** the dashboard is viewed on a screen narrower than 768 px
- **THEN** the sidebar collapses to a drawer and the main/results panels stack vertically

### Requirement: Job history view
The system SHALL provide a job history view listing all past resume sessions and their associated analysis/match/optimize results.

#### Scenario: History list loads on login
- **WHEN** the user accesses `/dashboard` after authentication
- **THEN** the sidebar fetches `GET /api/resumes/history` and displays resume filename, upload date, and available result types (analyze / match / optimize badges)

#### Scenario: Selecting a history item restores results
- **WHEN** the user clicks a history item
- **THEN** the results panel populates with the stored analysis or match output from the database without re-running the LLM

### Requirement: Frontend env var centralisation maintained
All environment-specific values (API base URL, OAuth client ID) SHALL be accessed exclusively through `frontend/src/config/env.js` (`ENV` object).

#### Scenario: OAuth client ID available at runtime
- **WHEN** the frontend initiates the OAuth flow
- **THEN** `ENV.GOOGLE_CLIENT_ID` is read from `VITE_GOOGLE_CLIENT_ID` — never hard-coded
