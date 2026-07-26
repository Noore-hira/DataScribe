from fastapi import APIRouter

router = APIRouter()


@router.delete("/session/{thread_id}")
async def clear_session(thread_id: str):

    return {
        "thread_id": thread_id,
        "status": "cleared",
    }