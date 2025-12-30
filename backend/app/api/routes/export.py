"""Export/download API endpoints."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.core.config import settings
from app.core.storage import load_job_status, get_output_dir
from app.models.job import JobState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


MIME_TYPES = {
    "txt": "text/plain",
    "json": "application/json",
    "pdf": "application/pdf",
}


@router.get("/{job_id}/{format}")
async def export_result(job_id: str, format: str):
    """
    Export/download the conversion result in the specified format.
    
    Supported formats: txt, json, pdf
    """
    # Validate format
    format = format.lower().strip(".")
    if format not in MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: {list(MIME_TYPES.keys())}",
        )
    
    # Check job status
    status = await load_job_status(job_id)
    
    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )
    
    state = status.get("state")
    
    if state != JobState.COMPLETED.value:
        raise HTTPException(
            status_code=409,
            detail=f"Job not complete. Current state: {state}",
        )
    
    # Find the output file
    output_dir = get_output_dir(job_id)
    file_path = output_dir / f"solfa.{format}"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Output file not found: {format}",
        )
    
    # Return the file
    return FileResponse(
        path=file_path,
        media_type=MIME_TYPES[format],
        filename=f"solfa_{job_id[:8]}.{format}",
    )


@router.get("/{job_id}/text")
async def get_text_result(job_id: str):
    """
    Get the solfa text result directly as a string.
    
    Useful for displaying in the frontend without downloading.
    """
    status = await load_job_status(job_id)
    
    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )
    
    result = status.get("result")
    
    if not result:
        raise HTTPException(
            status_code=409,
            detail="Result not yet available",
        )
    
    return {
        "job_id": job_id,
        "text": result.get("solfa_text", ""),
        "key": result.get("key_detected", ""),
        "time_signature": result.get("time_signature", ""),
        "measure_count": result.get("measure_count", 0),
    }

