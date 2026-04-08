## ADDED Requirements

### Requirement: Google OAuth 2.0 login flow
The system SHALL support Google OAuth 2.0 (PKCE + authorization code flow) as the only authentication method. The backend SHALL act as the OAuth client, handling the callback and issuing its own JWT tokens to the frontend.

#### Scenario: User initiates login
- **WHEN** a user clicks "Sign in with Google" on the landing page or any protected route
- **THEN** the frontend redirects to `GET /api/auth/google/login` which returns a Google authorization URL with a CSRF `state` parameter

#### Scenario: Successful OAuth callback
- **WHEN** Google redirects to `GET /api/auth/google/callback?code=...&state=...`
- **THEN** the backend validates `state`, exchanges `code` for Google tokens, upserts the user record in the database, issues a JWT access token (15-min TTL) and refresh token (30-day TTL) as HTTP-only `SameSite=Strict` cookies, and redirects the frontend to `/dashboard`

#### Scenario: Invalid or tampered state parameter
- **WHEN** the callback arrives with a `state` value that does not match the CSRF cookie
- **THEN** the backend returns HTTP 400 and does NOT create a session

#### Scenario: Token refresh
- **WHEN** the frontend makes a request and the access token is expired but the refresh token is valid
- **THEN** `POST /api/auth/refresh` issues a new access token and rotates the refresh token (old refresh token is immediately invalidated)

#### Scenario: Logout
- **WHEN** `POST /api/auth/logout` is called with a valid session
- **THEN** the refresh token is revoked in the database and both cookies are cleared

### Requirement: Protected route enforcement
The system SHALL enforce authentication on all `/api/resumes/*` and `/api/jobs/*` routes via a FastAPI auth middleware that validates the JWT.

#### Scenario: Missing or expired access token
- **WHEN** a request to a protected endpoint arrives with no valid JWT
- **THEN** the backend returns HTTP 401 `{ code: "UNAUTHENTICATED", status: "error" }`

#### Scenario: Valid authenticated request
- **WHEN** a request arrives with a valid JWT
- **THEN** `request.state.user_id` is populated and the handler proceeds normally

### Requirement: User identity stored during OAuth
The system SHALL upsert a user record on every successful OAuth callback using Google's `sub` (subject) as the stable identifier.

#### Scenario: First-time login creates user
- **WHEN** a Google account authenticates for the first time
- **THEN** a new `users` row is created with `google_sub`, `email`, `display_name`, `avatar_url`, and `created_at`

#### Scenario: Returning user login updates profile
- **WHEN** a returning user authenticates
- **THEN** `display_name`, `avatar_url`, and `last_login_at` are updated; no duplicate row is created
