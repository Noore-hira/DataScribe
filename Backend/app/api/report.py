from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/report/{filename}")
async def get_report(filename: str):

    safe_filename = Path(filename).name
    path = Path("storage/reports") / safe_filename

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    return FileResponse(path)