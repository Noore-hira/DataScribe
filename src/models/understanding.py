"""
understanding.py

Pydantic models representing the output of the
Data Understanding Agent.

The Understanding Agent uses the dataset metadata and
sample rows to infer the dataset's purpose, business
domain, possible machine learning task, and recommend
the next analysis steps.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DatasetDomain(str, Enum):
    """
    High-level business domain inferred by the LLM.
    """

    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    HUMAN_RESOURCES = "human_resources"
    MARKETING = "marketing"
    SALES = "sales"
    ECOMMERCE = "ecommerce"
    LOGISTICS = "logistics"
    UNKNOWN = "unknown"


class DatasetCategory(str, Enum):
    """
    Structural type of dataset.
    """

    TABULAR = "tabular"
    TIME_SERIES = "time_series"
    TEXT = "text"
    IMAGE_METADATA = "image_metadata"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class MLTask(str, Enum):
    """
    Machine learning task inferred from the dataset.
    """

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    FORECASTING = "forecasting"
    ANOMALY_DETECTION = "anomaly_detection"
    RECOMMENDATION = "recommendation"
    UNKNOWN = "unknown"


class TargetSuggestion(BaseModel):
    """
    Suggested target variable.
    """

    model_config = ConfigDict(extra="forbid")

    column: str

    confidence: float = Field(..., ge=0.0, le=1.0)

    reasoning: str


class AnalysisRecommendation(BaseModel):
    """
    Suggested analysis step.
    """

    model_config = ConfigDict(extra="forbid")

    title: str

    description: str

    priority: int = Field(..., ge=1, le=5)


class UnderstandingReport(BaseModel):
    """
    Structured output produced by the
    Data Understanding Agent.
    """

    model_config = ConfigDict(extra="forbid")

    dataset_summary: str = Field(
        ...,
        description="High-level summary of the dataset."
    )

    business_domain: DatasetDomain

    dataset_category: DatasetCategory

    ml_task: MLTask

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence of the understanding."
    )

    possible_targets: List[TargetSuggestion] = Field(
        default_factory=list
    )

    key_entities: List[str] = Field(
        default_factory=list,
        description="Important entities detected in the dataset."
    )

    important_columns: List[str] = Field(
        default_factory=list
    )

    potential_problems: List[str] = Field(
        default_factory=list
    )

    recommended_analyses: List[AnalysisRecommendation] = Field(
        default_factory=list
    )

    assumptions: List[str] = Field(
        default_factory=list
    )

    notes: Optional[str] = None