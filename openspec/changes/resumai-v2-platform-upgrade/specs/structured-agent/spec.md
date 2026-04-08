## ADDED Requirements

### Requirement: LangChain LCEL pipeline replaces direct Gemini calls
The system SHALL implement resume analysis, optimization, and job-description matching as LangChain LCEL (LangChain Expression Language) chains within a `LangChainProvider` class that conforms to the existing `BaseLLMProvider` interface.

#### Scenario: Provider registered and active via factory
- **WHEN** `LLM_PROVIDER=langchain` is set
- **THEN** the factory returns a `LangChainProvider` instance and all three operations (`analyze`, `optimize`, `match`) succeed end-to-end

#### Scenario: Chain invocation returns structured output
- **WHEN** `LangChainProvider.analyze(resume_text)` is called
- **THEN** the chain outputs a validated Pydantic model (matching existing `AnalysisResult` schema) — not a raw string

### Requirement: Prompt versioning via LangChain prompt templates
All prompts SHALL be defined as `ChatPromptTemplate` objects stored in `backend/app/services/prompt/` and versioned in source control.

#### Scenario: Prompt change is tracked
- **WHEN** a developer changes `builder.py` and commits
- **THEN** the change is visible in git diff and LangSmith traces reference the new prompt content

### Requirement: Model-agnostic chain configuration
The LangChain chain SHALL use `ChatGoogleGenerativeAI` as the default model, configurable via `LLM_MODEL_NAME` env var, so the model can be swapped without code changes.

#### Scenario: Model name configured via environment
- **WHEN** `LLM_MODEL_NAME=gemini-2.5-flash` is set (default)
- **THEN** the chain uses that model

#### Scenario: Alternative model swap
- **WHEN** `LLM_MODEL_NAME=gemini-1.5-pro` is set
- **THEN** the chain instantiates with that model and the rest of the pipeline is unchanged

### Requirement: Retry and error handling in chain
The chain SHALL wrap the LLM call with LangChain's built-in `with_retry` decorator (max 3 attempts, exponential back-off) and raise `LLMException` subclasses on unrecoverable failure.

#### Scenario: Transient 429 retried automatically
- **WHEN** the Gemini API returns HTTP 429 (rate limit)
- **THEN** the chain retries up to 3 times before raising `LLMRateLimitException`

#### Scenario: Non-retryable error raised immediately
- **WHEN** the Gemini API returns HTTP 400 (bad request)
- **THEN** the chain raises `LLMInvalidRequestException` without retrying
