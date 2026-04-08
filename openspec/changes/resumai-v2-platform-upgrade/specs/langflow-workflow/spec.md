## ADDED Requirements

### Requirement: Langflow used for offline workflow design only
The system SHALL treat Langflow as a design and prototyping tool. Langflow flows SHALL be exported as JSON, translated to LangChain LCEL Python code, and committed to source control. Langflow SHALL NOT run in production.

#### Scenario: Langflow flow exported and committed
- **WHEN** a developer designs or updates an agent workflow in Langflow
- **THEN** the exported JSON is saved to `backend/app/services/llm/flows/` and the corresponding LCEL implementation is updated in `langchain_provider.py`

#### Scenario: Langflow not present in production Docker image
- **WHEN** the production Docker image is built
- **THEN** `langflow` is NOT listed in `pyproject.toml` production dependencies (only in `[tool.poetry.group.dev.dependencies]`)

### Requirement: Langflow runs locally via Docker for team design sessions
A `docker-compose.langflow.yml` SHALL be provided to spin up a local Langflow instance for design sessions.

#### Scenario: Developer starts Langflow locally
- **WHEN** `docker compose -f docker-compose.langflow.yml up` is run
- **THEN** Langflow is accessible at `http://localhost:7860`

### Requirement: Flow files versioned in source control
All Langflow JSON export files in `backend/app/services/llm/flows/` SHALL be committed to git with meaningful commit messages describing the workflow change.

#### Scenario: Flow change is reviewable
- **WHEN** a flow JSON file is modified and a PR is opened
- **THEN** the git diff clearly shows which nodes or connections changed
