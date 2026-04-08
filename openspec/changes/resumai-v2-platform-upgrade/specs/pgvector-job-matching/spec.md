## ADDED Requirements

### Requirement: Resume and JD embeddings stored in pgvector
The system SHALL generate 768-dimension embeddings for uploaded resumes and submitted job descriptions using Google's `text-embedding-004` model via the LangChain embeddings interface, and store them in `vector(768)` columns in PostgreSQL.

#### Scenario: Resume embedding generated on upload
- **WHEN** a resume is uploaded and parsed to Markdown
- **THEN** an embedding is generated and stored in `resume_sessions.content_embedding`

#### Scenario: JD embedding generated on match request
- **WHEN** `POST /api/resumes/match` is called with a job description
- **THEN** a JD embedding is generated and stored in the associated `match_results` row

### Requirement: Cosine similarity match scoring
The system SHALL compute the job-description match score using cosine similarity (`<=>` operator) between the resume embedding and JD embedding via a pgvector SQL query.

#### Scenario: Semantic match returns ranked score
- **WHEN** `POST /api/resumes/match` completes
- **THEN** the response includes `semantic_score` (0.0–1.0, cosine similarity) in addition to the existing LLM-generated `match_analysis`

#### Scenario: Match score reflects semantic similarity
- **WHEN** a resume closely matches the JD in domain vocabulary and experience
- **THEN** `semantic_score` is ≥ 0.7

### Requirement: Approximate nearest-neighbour index for scale
The pgvector table SHALL have an `ivfflat` index on the embedding column with `lists=100` to maintain sub-100 ms query latency as the dataset grows.

#### Scenario: Index applied in migration
- **WHEN** Alembic applies the pgvector migration
- **THEN** the `ivfflat` index is created on `resume_sessions.content_embedding`

### Requirement: Embedding generation is non-blocking
Embedding generation SHALL occur inside the async job worker, not in the HTTP request handler, to avoid adding latency to the upload response.

#### Scenario: Upload response is immediate even with embedding
- **WHEN** a resume is uploaded
- **THEN** the upload endpoint returns within 2 s; embedding generation happens asynchronously in the Cloud Tasks worker
