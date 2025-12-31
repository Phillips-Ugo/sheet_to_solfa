"""Job status and processing models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobState(str, Enum):
    """Processing job states."""

    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    OMR_PROCESSING = "omr_processing"
    ANALYZING = "analyzing"
    CONVERTING = "converting"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(BaseModel):
    """Status of a processing job."""

    job_id: str
    state: JobState = JobState.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None
    result: dict[str, Any] | None = None

    class Config:
        use_enum_values = True


class JobCreate(BaseModel):
    """Response when creating a new job."""

    job_id: str
    message: str = "Processing started"


class JobResult(BaseModel):
    """Final result of a completed job."""

    job_id: str
    solfa_text: str
    key_detected: str
    time_signature: str
    measure_count: int
    note_count: int
    available_formats: list[str] = ["txt", "json", "pdf"]


