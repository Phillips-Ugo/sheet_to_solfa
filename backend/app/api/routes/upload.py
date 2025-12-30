"""Upload API endpoint for PDF files."""

import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.core.storage import save_upload, save_job_status
from app.models.job import JobCreate, JobState
from app.workers.processor import process_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """Response for file upload."""

    job_id: str
    message: str
    filename: str


@router.post("", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload a PDF file for processing.
    
    Accepts PDF files and initiates background processing.
    Returns a job ID for tracking the conversion progress.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted",
        )
    
    # Check file size
    content = await file.read()
    max_size = settings.max_file_size_mb * 1024 * 1024
    
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB",
        )
    
    # Save the uploaded file
    try:
        settings.ensure_directories()
        job_id, file_path = await save_upload(content, file.filename)
        
        # Initialize job status
        await save_job_status(
            job_id,
            {
                "job_id": job_id,
                "state": JobState.PENDING.value,
                "progress": 0,
                "message": "Upload complete, queued for processing",
            },
        )
        
        # Start background processing
        background_tasks.add_task(process_job, job_id, file_path)
        
        logger.info(f"Uploaded file {file.filename} as job {job_id}")
        
        return UploadResponse(
            job_id=job_id,
            message="File uploaded successfully. Processing started.",
            filename=file.filename,
        )
        
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}",
        )


@router.post("/test", response_model=UploadResponse)
async def upload_test(background_tasks: BackgroundTasks):
    """
    Test endpoint that creates a mock job for testing.
    
    Useful for testing the frontend without actual PDF processing.
    """
    import uuid
    from datetime import datetime
    
    job_id = str(uuid.uuid4())
    
    settings.ensure_directories()
    
    # Create mock job status
    await save_job_status(
        job_id,
        {
            "job_id": job_id,
            "state": JobState.PENDING.value,
            "progress": 0,
            "message": "Test job created",
        },
    )
    
    # Simulate processing in background
    async def mock_process(job_id: str):
        import asyncio
        
        states = [
            (JobState.PREPROCESSING, 10, "Extracting pages..."),
            (JobState.PREPROCESSING, 25, "Preprocessing images..."),
            (JobState.OMR_PROCESSING, 45, "Running OMR..."),
            (JobState.ANALYZING, 65, "Parsing notation..."),
            (JobState.CONVERTING, 80, "Converting to solfa..."),
            (JobState.RENDERING, 95, "Generating output..."),
        ]
        
        for state, progress, message in states:
            await asyncio.sleep(1)
            await save_job_status(
                job_id,
                {
                    "job_id": job_id,
                    "state": state.value,
                    "progress": progress,
                    "message": message,
                },
            )
        
        # Complete with mock result
        await save_job_status(
            job_id,
            {
                "job_id": job_id,
                "state": JobState.COMPLETED.value,
                "progress": 100,
                "message": "Processing complete!",
                "result": {
                    "solfa_text": "| d r m f | s l t d' |\n| d' t l s | f m r d |",
                    "key_detected": "C major",
                    "time_signature": "4/4",
                    "measure_count": 2,
                    "note_count": 16,
                    "available_formats": ["txt", "json", "pdf"],
                },
            },
        )
    
    background_tasks.add_task(mock_process, job_id)
    
    return UploadResponse(
        job_id=job_id,
        message="Test job created. Mock processing started.",
        filename="test.pdf",
    )

