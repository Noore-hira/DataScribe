from pathlib import Path
import shutil

from fastapi import APIRouter, File, UploadFile, HTTPException

router = APIRouter()

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
):

    suffix = Path(file.filename).suffix.lower()

    if suffix not in [".csv", ".xlsx", ".xls", ".parquet"]:

        raise HTTPException(
            status_code=400,
            detail="Unsupported file type.",
        )

    save_path = UPLOAD_DIR / file.filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "path": str(save_path),
        "status": "uploaded",
    }