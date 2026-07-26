from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from Backend.app.services.stream_service import stream_chat

router = APIRouter()


@router.get("/chat/stream")
async def chat_stream(
    message: str,
    thread_id: str,
    api_key: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    """
    Server-Sent Events endpoint for streaming graph execution.

    The response uses ``text/event-stream`` so that the browser's
    ``EventSource`` API can consume it.  Heartbeat events are sent
    every 10 seconds to keep the connection alive during long-running
    LLM operations, and any exception in the graph workflow is
    forwarded to the client as an ``error`` event instead of silently
    closing the connection.
    """

    return EventSourceResponse(
        stream_chat(
            query=message,
            thread_id=thread_id,
            api_key=api_key,
            model=model,
        ),
        media_type="text/event-stream",
        headers={
            # Disable buffering so events are sent immediately
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
