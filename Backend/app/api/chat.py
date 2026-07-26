from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse


from Backend.app.services.stream_service import stream_chat

router = APIRouter(prefix="/api")


@router.get("/chat/stream")
async def chat_stream(
    message: str,
    thread_id: str,
):

    return EventSourceResponse(
        stream_chat(
            query=message,
            thread_id=thread_id,
        )
    )