from fastapi import APIRouter

router = APIRouter()


@router.get("/history")
async def get_history():
    """
    Returns a list of past chat threads.
    Currently returns an empty list since the backend does not
    persist sessions. Session history is managed client-side
    via Supabase.
    """
    return {"threads": []}


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """
    Returns details for a specific thread.
    Currently returns basic metadata since the backend does not
    persist sessions.
    """
    return {
        "thread_id": thread_id,
        "title": "",
        "filename": None,
        "rows": 0,
        "columns": 0,
    }


@router.delete("/session/{thread_id}")
async def clear_session(thread_id: str):

    return {
        "thread_id": thread_id,
        "status": "cleared",
    }
