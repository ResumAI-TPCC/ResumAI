## ADDED Requirements

### Requirement: LangSmith tracing enabled for all LangChain operations
The system SHALL send traces for every LangChain chain invocation to LangSmith when `LANGCHAIN_TRACING_V2=true` is set.

#### Scenario: Trace appears in LangSmith on chain invocation
- **WHEN** `LangChainProvider.analyze(...)` is called in an environment with tracing enabled
- **THEN** a trace is visible in the configured LangSmith project within 30 seconds, including input, output, model name, latency, and token counts

#### Scenario: No tracing in local dev by default
- **WHEN** `LANGCHAIN_TRACING_V2` is unset or `false`
- **THEN** no data is sent to LangSmith; the chain behaves identically

### Requirement: LangSmith project and API key configured via environment
The system SHALL read `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, and `LANGCHAIN_TRACING_V2` from the environment (via `get_settings()`), never hard-coded.

#### Scenario: Missing LangSmith key does not crash the app
- **WHEN** `LANGCHAIN_API_KEY` is absent and `LANGCHAIN_TRACING_V2=false`
- **THEN** the application starts and operates normally; no exception is raised

### Requirement: Token usage and latency tracked per operation type
Each LangSmith trace SHALL include a `run_name` tag matching the operation (`analyze`, `optimize`, `match`) for dashboard filtering.

#### Scenario: Operation-level filtering in LangSmith
- **WHEN** filtering the LangSmith project by `run_name=analyze`
- **THEN** only analysis chain traces are returned
