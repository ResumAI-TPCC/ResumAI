"""
Chat API Routes
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """
    Chat completion endpoint

    Send a list of messages, get AI response

    TODO: Implement after integrating actual LLM Provider
    """
    # Skeleton implementation: return 200 OK placeholder response
    return ChatResponse(
        content="[Placeholder] LLM response will be here",
        model="not-configured",
        usage=None,
    )


@router.post("/completions/stream")
async def chat_completions_stream(request: ChatRequest):
    """
    Streaming chat completion endpoint

    TODO: Implement after integrating actual LLM Provider
    """
    # Skeleton implementation: return 200 OK placeholder streaming response
    async def _placeholder_stream():
        yield "data: [Placeholder] Streaming not implemented yet\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _placeholder_stream(),
        media_type="text/event-stream",
    )

