from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


# ─── Job Schemas ──────────────────────────────────────────────────────────────

class JobStatus(BaseModel):
    id: str
    podcast_id: Optional[str] = None
    stage: str
    progress: float
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Transcript Schemas ────────────────────────────────────────────────────────

class TranscriptSegmentSchema(BaseModel):
    id: str
    podcast_id: str
    segment_index: int
    start_time: float
    end_time: float
    text: str
    topic_id: Optional[int] = None
    topic_label: Optional[str] = None
    confidence: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Chapter Schemas ───────────────────────────────────────────────────────────

class ChapterSchema(BaseModel):
    id: str
    podcast_id: str
    chapter_number: int
    title: str
    start_time: float
    end_time: float
    topic_id: Optional[int] = None
    topic_label: Optional[str] = None
    topic_keywords: Optional[str] = None
    summary: Optional[str] = None
    segment_ids: Optional[str] = None
    is_edited: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None


# ─── Podcast Schemas ───────────────────────────────────────────────────────────

class PodcastListItem(BaseModel):
    id: str
    job_id: str
    title: str
    original_filename: str
    duration_seconds: Optional[float] = None
    word_count: Optional[int] = None
    topic_count: Optional[int] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PodcastDetail(BaseModel):
    id: str
    job_id: str
    title: str
    filename: str
    original_filename: str
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    audio_format: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    word_count: Optional[int] = None
    topic_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ─── Upload Response ───────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    job_id: str
    podcast_id: str
    message: str


# ─── Stats Schema ─────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_podcasts: int
    completed_podcasts: int
    total_duration_seconds: float
    total_chapters: int
    total_words: int
