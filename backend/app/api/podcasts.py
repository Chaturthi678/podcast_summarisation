"""
Podcast API routes.
"""
import json
import logging
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.database import get_db, Podcast, ProcessingJob, TranscriptSegment, Chapter
from app.schemas import (
    UploadResponse, PodcastListItem, PodcastDetail,
    TranscriptSegmentSchema, ChapterSchema, ChapterUpdate, DashboardStats, JobStatus
)
from app.workers.processing import submit_job

router = APIRouter(prefix="/api/podcasts", tags=["podcasts"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# ─── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_podcast(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an audio file and start background AI processing."""
    # Treat client filenames as labels only; never use them for storage paths.
    original_name = (file.filename or "Untitled").replace("\\", "/").rsplit("/", 1)[-1]
    original_name = "".join(char for char in original_name if char.isprintable()).strip()[:255] or "Untitled"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Generate IDs and save file
    podcast_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    safe_name = f"{podcast_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    size_bytes = 0
    try:
        with open(file_path, "wb") as target:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > MAX_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB upload limit.",
                    )
                target.write(chunk)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    finally:
        await file.close()

    if size_bytes == 0:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Derive title from filename
    title = os.path.splitext(original_name)[0].replace("_", " ").replace("-", " ").strip().title()[:160] or "Untitled"

    # Create Podcast record
    podcast = Podcast(
        id=podcast_id,
        job_id=job_id,
        title=title,
        filename=safe_name,
        original_filename=original_name,
        file_path=file_path,
        file_size_bytes=size_bytes,
        status="pending",
    )
    db.add(podcast)

    # Create Job record
    job = ProcessingJob(
        id=job_id,
        podcast_id=podcast_id,
        stage="queued",
        progress=0.0,
        message="Job queued",
    )
    db.add(job)
    try:
        db.commit()
    except Exception:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    # Submit to background worker
    submit_job(job_id, podcast_id, file_path)

    return UploadResponse(
        job_id=job_id,
        podcast_id=podcast_id,
        message="Upload successful. Processing started.",
    )


# ─── List & Detail ────────────────────────────────────────────────────────────

@router.get("", response_model=List[PodcastListItem])
def list_podcasts(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List a bounded page of podcasts, newest first."""
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    pods = db.query(Podcast).order_by(Podcast.created_at.desc()).offset(offset).limit(limit).all()
    return pods


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """Dashboard statistics."""
    total = db.query(Podcast).count()
    completed = db.query(Podcast).filter(Podcast.status == "completed").count()
    total_dur = db.query(func.coalesce(func.sum(Podcast.duration_seconds), 0)).filter(Podcast.status == "completed").scalar()
    total_chapters = db.query(Chapter).count()
    total_words = db.query(func.coalesce(func.sum(Podcast.word_count), 0)).filter(Podcast.status == "completed").scalar()
    return DashboardStats(
        total_podcasts=total,
        completed_podcasts=completed,
        total_duration_seconds=total_dur,
        total_chapters=total_chapters,
        total_words=total_words,
    )


@router.get("/{podcast_id}", response_model=PodcastDetail)
def get_podcast(podcast_id: str, db: Session = Depends(get_db)):
    """Get full podcast details including chapters and transcript."""
    pod = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not pod:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return pod


@router.post("/{podcast_id}/retry", response_model=JobStatus)
def retry_podcast(podcast_id: str, db: Session = Depends(get_db)):
    """Retry a failed episode when it has not produced partial results."""
    pod = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not pod:
        raise HTTPException(status_code=404, detail="Podcast not found")
    if pod.status != "failed":
        raise HTTPException(status_code=409, detail="Only failed episodes can be retried")
    if not os.path.isfile(pod.file_path):
        raise HTTPException(status_code=404, detail="The uploaded audio file is no longer available")
    if db.query(TranscriptSegment).filter(TranscriptSegment.podcast_id == podcast_id).count() or db.query(Chapter).filter(Chapter.podcast_id == podcast_id).count():
        raise HTTPException(status_code=409, detail="This episode already has partial results. Please review them before retrying.")
    job = db.query(ProcessingJob).filter(ProcessingJob.id == pod.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    job.stage = "queued"
    job.progress = 0.0
    job.message = "Retry queued"
    job.error = None
    job.updated_at = datetime.now(timezone.utc)
    pod.status = "pending"
    pod.error_message = None
    db.commit()
    submit_job(job.id, pod.id, pod.file_path)
    db.refresh(job)
    return job


@router.get("/{podcast_id}/transcript", response_model=List[TranscriptSegmentSchema])
def get_transcript(podcast_id: str, db: Session = Depends(get_db)):
    """Get transcript segments for a podcast."""
    segs = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.podcast_id == podcast_id)
        .order_by(TranscriptSegment.segment_index)
        .all()
    )
    return segs


@router.get("/{podcast_id}/chapters", response_model=List[ChapterSchema])
def get_chapters(podcast_id: str, db: Session = Depends(get_db)):
    """Get chapters for a podcast."""
    chs = (
        db.query(Chapter)
        .filter(Chapter.podcast_id == podcast_id)
        .order_by(Chapter.chapter_number)
        .all()
    )
    return chs


@router.patch("/{podcast_id}/chapters/{chapter_id}", response_model=ChapterSchema)
def update_chapter(
    podcast_id: str,
    chapter_id: str,
    update: ChapterUpdate,
    db: Session = Depends(get_db),
):
    """Update a chapter title or summary."""
    ch = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id, Chapter.podcast_id == podcast_id)
        .first()
    )
    if not ch:
        raise HTTPException(status_code=404, detail="Chapter not found")
    if update.title is not None:
        ch.title = update.title
    if update.summary is not None:
        ch.summary = update.summary
    ch.is_edited = True
    db.commit()
    db.refresh(ch)
    return ch


# ─── Downloads ────────────────────────────────────────────────────────────────

@router.get("/{podcast_id}/audio")
def stream_audio(podcast_id: str, db: Session = Depends(get_db)):
    """Serve the original uploaded audio file."""
    pod = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not pod:
        raise HTTPException(status_code=404, detail="Podcast not found")
    if not os.path.exists(pod.file_path):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    return FileResponse(
        pod.file_path,
        media_type=mimetypes.guess_type(pod.original_filename or pod.file_path)[0] or "application/octet-stream",
    )


@router.get("/{podcast_id}/download/{format}")
def download_export(podcast_id: str, format: str, db: Session = Depends(get_db)):
    """Download export files: txt | md | json | mp3"""
    pod = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not pod:
        raise HTTPException(status_code=404, detail="Podcast not found")
    if pod.status != "completed":
        raise HTTPException(status_code=400, detail="Processing not yet complete")

    output_dir = os.path.join(settings.OUTPUT_DIR, podcast_id)

    format_map = {
        "txt": ("transcript.txt", "text/plain"),
        "md": ("chapters.md", "text/markdown"),
        "json": ("analysis.json", "application/json"),
        "mp3": ("podcast_chapters.mp3", "audio/mpeg"),
    }

    if format not in format_map:
        raise HTTPException(status_code=400, detail=f"Unknown format '{format}'. Use: txt, md, json, mp3")

    filename, media_type = format_map[format]
    file_path = os.path.join(output_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Export file '{filename}' not found. Try re-processing.")

    return FileResponse(file_path, media_type=media_type, filename=filename)
