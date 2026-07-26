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

    return {
        "filename": file.filename,
        "path": str(save_path),
        "status": "uploaded",
        "rows": len(df),
        "columns": len(df.columns),
        "thread_id": str(uuid.uuid4()),
    }
