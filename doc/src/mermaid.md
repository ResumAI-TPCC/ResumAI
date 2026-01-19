'''mermaid
data1:
flowchart TD
    A[Frontend] -->|Resume| B[Backend]
    B[Backend] -->|session_id| A[Frontend]
    
    B[Backend] -->|Resume| C[GCS]
    C[GCS] -->|id| B[Backend]

data2:
flowchart TD
    A[Frontend] -->|Request with seesion_id| B[Backend]
    B[Backend] -->|Response| A[Frontend]
    
    B[Backend] -->|id| C[GCS]
    C[GCS] -->|Resume| B[Backend]

    B[Backend] -->|Request with Resume| D[LLM]
    D[LLM] -->|Response| B[Backend]  

architecture:
architecture-beta
    group backend(cloud)[Backend]

    service router(server)[API_Router] in backend
    service session(server)[session_service] in backend
    service resume(server)[resume_service] in backend
    service provider(server)[LLM_Provider] in backend
    service llm(internet)[llm]
    service gcs(cloud)[gcs]
    service frontend(server)[Frontend] 
    

    router:L -- R:session
    router:B -- T:resume
    router:T -- B:frontend
    session:L -- R:gcs
    resume:L -- R:provider
    provider:L -- R:llm  
'''