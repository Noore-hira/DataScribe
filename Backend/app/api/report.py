from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/report/{filename}")
async def get_report(filename: str):

    path = Path("storage/reports") / filename

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    return FileResponse(path)