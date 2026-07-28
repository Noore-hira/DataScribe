from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.delete("/session/{thread_id}")
async def clear_session(thread_id: str):
    """
    Clear all files associated with a given thread_id.

    Removes uploaded datasets and generated reports/charts
    that belong to the session, then returns a summary.
    """
    removed = []

    # Remove uploaded files that match the thread_id prefix
    if UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.iterdir():
            if thread_id in f.name:
                try:
                    f.unlink()
                    removed.append(f.name)
                except Exception:
                    pass

    # Clear generated charts and reports directories
    for dir_name in ("charts", "storage/charts", "storage/reports"):
        d = Path(dir_name)
        if d.exists():
            for f in d.iterdir():
                if thread_id in f.name:
                    try:
                        f.unlink()
                        removed.append(str(f))
                    except Exception:
                        pass

    return {
        "thread_id": thread_id,
        "status": "cleared",
        "removed_files": removed,
    }
