"""Local file storage utilities."""

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles

from app.core.config import settings


async def save_upload(file_content: bytes, filename: str) -> tuple[str, Path]:
    """
    Save uploaded file and return job_id and file path.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        
    Returns:
        Tuple of (job_id, saved_file_path)
    """
    job_id = str(uuid.uuid4())
    job_dir = settings.upload_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Preserve original extension
    ext = Path(filename).suffix or ".pdf"
    file_path = job_dir / f"input{ext}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)

    return job_id, file_path


def get_job_dir(job_id: str) -> Path:
    """Get the directory for a specific job."""
    return settings.upload_dir / job_id


def get_output_dir(job_id: str) -> Path:
    """Get the output directory for a specific job."""
    output_dir = settings.output_dir / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_job_status_sync(job_id: str, status: dict[str, Any]) -> None:
    """Save job status to JSON file (synchronous version)."""
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    status_file = settings.jobs_dir / f"{job_id}.json"
    status["updated_at"] = datetime.utcnow().isoformat()

    content = json.dumps(status, indent=2, default=str)
    
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()


async def save_job_status(job_id: str, status: dict[str, Any]) -> None:
    """Save job status to JSON file."""
    # Use synchronous write for reliability on Windows
    save_job_status_sync(job_id, status)


async def load_job_status(job_id: str) -> dict[str, Any] | None:
    """Load job status from JSON file."""
    status_file = settings.jobs_dir / f"{job_id}.json"

    if not status_file.exists():
        return None

    try:
        async with aiofiles.open(status_file, "r") as f:
            content = await f.read()
            
        # Handle empty file (race condition during write)
        if not content or not content.strip():
            return {
                "job_id": job_id,
                "state": "pending",
                "progress": 0,
                "message": "Initializing...",
            }
            
        return json.loads(content)
    except json.JSONDecodeError:
        # File is being written, return pending status
        return {
            "job_id": job_id,
            "state": "pending",
            "progress": 0,
            "message": "Initializing...",
        }
    except Exception:
        return None


def cleanup_job(job_id: str) -> None:
    """Remove all files associated with a job."""
    job_dir = settings.upload_dir / job_id
    output_dir = settings.output_dir / job_id
    status_file = settings.jobs_dir / f"{job_id}.json"

    if job_dir.exists():
        shutil.rmtree(job_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if status_file.exists():
        status_file.unlink()

