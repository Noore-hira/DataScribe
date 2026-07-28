import json
from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from Backend.app.services.stream_service import stream_chat

router = APIRouter()

async def _gatekeeper_stream(friendly_message: str):
    """
    Yields a friendly chat message to the frontend and gracefully completes 
    the SSE stream so the workflow doesn't get triggered.
    """
    yield {
        "event": "message",
        "data": json.dumps({"content": friendly_message})
    }
    yield {
        "event": "complete",
        "data": json.dumps({"duration": 0})
    }

@router.get("/chat/stream")
async def chat_stream(
    request: Request,
    message: str,
    thread_id: str,
    api_key: str | None = Query(default=None),
    model: str | None = Query(default=None),
    dataset_path: str | None = Query(default=None),
):
    """
    Server-Sent Events endpoint for streaming graph execution.
    """

    # Validate core input
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if len(message) > 10000:
        raise HTTPException(status_code=400, detail="Message too long. Maximum 10,000 characters.")
    if not thread_id or not thread_id.strip():
        raise HTTPException(status_code=400, detail="Thread ID is required.")

    # ---------------------------------------------------------
    # GATEKEEPER: Check for API Key ONLY
    # ---------------------------------------------------------
    if not api_key or not api_key.strip():
        return EventSourceResponse(
            _gatekeeper_stream("Please provide your Groq API key in the settings panel to continue!"),
            media_type="text/event-stream"
        )
    # ---------------------------------------------------------

    return EventSourceResponse(
        stream_chat(
            query=message,
            thread_id=thread_id,
            api_key=api_key,
            model=model,
            dataset_path=dataset_path,
        ),
        media_type="text/event-stream",
        headers={
            # Disable buffering so events are sent immediately
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )