import uuid
from pathlib import Path
import shutil

import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException

router = APIRouter()

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...), # <-- Removed max_length here
):
    # --- NEW: Safely check the file size (25 MB limit) ---
    MAX_SIZE = 25 * 1024 * 1024
    if file.size and file.size > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 25MB."
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File must have a filename."
        )

    suffix = Path(file.filename).suffix.lower()

    if suffix not in [".csv", ".xlsx", ".xls", ".parquet"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type.",
        )

    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    save_path = UPLOAD_DIR / safe_name

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read the file to extract row/column metadata
    try:
        if suffix == ".csv":
            df = pd.read_csv(save_path)
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(save_path)
        elif suffix == ".parquet":
            df = pd.read_parquet(save_path)
        else:
            df = pd.DataFrame()
    except Exception:
        df = pd.DataFrame()
        # Clean up the saved file if reading failed
        try:
            save_path.unlink()
        except Exception:
            pass

    return {
        "filename": file.filename,
        "path": str(save_path),
        "status": "uploaded",
        "rows": len(df),
        "columns": len(df.columns),
        "thread_id": str(uuid.uuid4()),
    }