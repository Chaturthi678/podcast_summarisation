from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime, ForeignKey, Boolean, Index, event
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
import uuid

from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,
)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
    # create_all does not add indexes to existing databases; ensure these query
    # paths are indexed for both clean installs and upgrades of local databases.
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            index.create(bind=engine, checkfirst=True)


# ─── DB Models ────────────────────────────────────────────────────────────────

class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    audio_format = Column(String, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    topic_count = Column(Integer, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    segments = relationship("TranscriptSegment", back_populates="podcast", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="podcast", cascade="all, delete-orphan")
    job = relationship("ProcessingJob", back_populates="podcast", uselist=False, cascade="all, delete-orphan")


Index("ix_podcasts_status_created", Podcast.status, Podcast.created_at)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True)
    podcast_id = Column(String, ForeignKey("podcasts.id"), nullable=True)
    stage = Column(String, default="queued")  # queued, uploading, preprocessing, transcribing, detecting_topics, generating_summaries, writing_metadata, completed, failed
    progress = Column(Float, default=0.0)   # 0.0 – 1.0
    message = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    podcast = relationship("Podcast", back_populates="job")


Index("ix_jobs_stage_updated", ProcessingJob.stage, ProcessingJob.updated_at)


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    podcast_id = Column(String, ForeignKey("podcasts.id"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    topic_id = Column(Integer, nullable=True)
    topic_label = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

    podcast = relationship("Podcast", back_populates="segments")


Index("ix_segments_podcast_index", TranscriptSegment.podcast_id, TranscriptSegment.segment_index)


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    podcast_id = Column(String, ForeignKey("podcasts.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    topic_id = Column(Integer, nullable=True)
    topic_label = Column(String, nullable=True)
    topic_keywords = Column(Text, nullable=True)   # JSON array stored as text
    summary = Column(Text, nullable=True)
    segment_ids = Column(Text, nullable=True)      # JSON array of segment IDs
    is_edited = Column(Boolean, default=False)

    podcast = relationship("Podcast", back_populates="chapters")


Index("ix_chapters_podcast_number", Chapter.podcast_id, Chapter.chapter_number)
