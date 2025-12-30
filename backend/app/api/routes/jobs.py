"""Job status API endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.storage import load_job_status
from app.models.job import JobState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobStatusResponse(BaseModel):
    """Response for job status query."""

    job_id: str
    state: str
    progress: float
    message: str
    error: str | None = None
    result: dict[str, Any] | None = None
    updated_at: str | None = None


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the current status of a processing job.
    
    Returns the job state, progress percentage, and any results or errors.
    """
    status = await load_job_status(job_id)
    
    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )
    
    return JobStatusResponse(
        job_id=status.get("job_id", job_id),
        state=status.get("state", JobState.PENDING.value),
        progress=status.get("progress", 0),
        message=status.get("message", ""),
        error=status.get("error"),
        result=status.get("result"),
        updated_at=status.get("updated_at"),
    )


@router.get("/{job_id}/result")
async def get_job_result(job_id: str):
    """
    Get the result of a completed job.
    
    Only available for jobs in COMPLETED state.
    """
    status = await load_job_status(job_id)
    
    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )
    
    state = status.get("state")
    
    if state == JobState.FAILED.value:
        raise HTTPException(
            status_code=422,
            detail=f"Job failed: {status.get('error', 'Unknown error')}",
        )
    
    if state != JobState.COMPLETED.value:
        raise HTTPException(
            status_code=409,
            detail=f"Job not yet complete. Current state: {state}",
        )
    
    result = status.get("result")
    
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Job completed but no result available",
        )
    
    return result

