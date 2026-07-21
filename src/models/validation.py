"""
validation.py

Pydantic models representing the dataset validation results.

These models are used by the Dataset Validator node to provide
structured information about uploaded datasets.

Author: DataScribe
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DatasetType(str, Enum):
    """Supported dataset types."""

    CSV = "csv"
    EXCEL = "excel"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    """Validation status."""

    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"


class ColumnInfo(BaseModel):
    """
    Metadata for a single dataframe column.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Column name")

    dtype: str = Field(..., description="Detected pandas datatype")

    missing_values: int = Field(
        default=0,
        ge=0,
        description="Number of missing values",
    )

    unique_values: int = Field(
        default=0,
        ge=0,
        description="Number of unique values",
    )

    is_numeric: bool = False

    is_datetime: bool = False

    is_categorical: bool = False


class DatasetMetadata(BaseModel):
    """
    General information about the uploaded dataset.
    """

    model_config = ConfigDict(extra="forbid")

    file_name: str

    dataset_type: DatasetType

    rows: int = Field(..., ge=0)

    columns: int = Field(..., ge=0)

    memory_usage_mb: float = Field(..., ge=0)

    duplicate_rows: int = Field(..., ge=0)

    duplicate_columns: List[str] = Field(default_factory=list)

    encoding: Optional[str] = None

    delimiter: Optional[str] = None


class ValidationIssue(BaseModel):
    """
    Represents one validation warning or error.
    """

    model_config = ConfigDict(extra="forbid")

    severity: str

    message: str

    recommendation: Optional[str] = None


class ValidationReport(BaseModel):
    """
    Output produced by the Dataset Validator node.

    This report is stored directly inside GraphState.
    """

    model_config = ConfigDict(extra="forbid")

    status: ValidationStatus

    is_valid: bool

    metadata: DatasetMetadata

    columns: List[ColumnInfo] = Field(default_factory=list)

    issues: List[ValidationIssue] = Field(default_factory=list)

    summary: str = ""

    execution_time: float = Field(
        default=0.0,
        ge=0,
        description="Execution time in seconds",
    )