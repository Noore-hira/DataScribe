import os
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent

def load_dataframe(file_path: str | None = None) -> pd.DataFrame:
    """Return a new dataset for each graph run.
    
    Strictly requires a file_path to be provided by the user via the frontend.
    """
    if not file_path:
        raise ValueError("No dataset provided. Please upload a dataset first.")
        
    resolved = Path(file_path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
        
    if not resolved.exists():
        raise FileNotFoundError(f"Dataset not found at {resolved}")
        
    return pd.read_csv(resolved)