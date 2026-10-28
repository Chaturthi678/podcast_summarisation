"""
Background processing worker.
Runs the full AI pipeline in a thread pool so the API stays responsive.
"""
import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, Podcast, ProcessingJob, TranscriptSegment, Chapter

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=settings.PROCESSING_WORKERS, thread_name_prefix="podly-worker")


# ─── Job helpers ──────────────────────────────────────────────────────────────

def _get_job(db: Session, job_id: str) -> Optional[ProcessingJob]:
    return db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()


def _update_job(
    job_id: str,
    stage: str,
    progress: float,
    message: str = "",
    error: Optional[str] = None,
):
    """Update job status in DB. Creates its own session for thread safety."""
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.stage = stage
            job.progress = progress
            job.message = message
            job.error = error
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _update_podcast(podcast_id: str, **kwargs):
    db = SessionLocal()
    try:
        pod = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if pod:
            for k, v in kwargs.items():
                setattr(pod, k, v)
            db.commit()
    finally:
        db.close()


def _save_segments(podcast_id: str, segments: list):
    db = SessionLocal()
    try:
        for seg in segments:
            db_seg = TranscriptSegment(
                podcast_id=podcast_id,
                segment_index=seg["id"],
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],
                topic_id=seg.get("topic_id"),
                topic_label=seg.get("topic_label"),
            )
            db.add(db_seg)
        db.commit()
    finally:
        db.close()


def _save_chapters(podcast_id: str, chapters: list):
    db = SessionLocal()
    try:
        for ch in chapters:
            seg_ids = [str(s.get("id", "")) for s in ch.get("segments", [])]
            keywords = ", ".join(ch.get("topic_label", "").split(",")[:5])
            db_ch = Chapter(
                id=str(uuid.uuid4()),
                podcast_id=podcast_id,
                chapter_number=ch["chapter_number"],
                title=ch.get("title", f"Chapter {ch['chapter_number']}"),
                start_time=ch["start_time"],
                end_time=ch["end_time"],
                topic_id=ch.get("topic_id"),
                topic_label=ch.get("topic_label"),
                topic_keywords=keywords,
                summary=ch.get("summary"),
                segment_ids=json.dumps(seg_ids),
            )
            db.add(db_ch)
        db.commit()
    finally:
        db.close()


def _clear_partial_results(podcast_id: str):
    """Keep failed jobs retryable when a later pipeline stage fails."""
    db = SessionLocal()
    try:
        db.query(TranscriptSegment).filter(TranscriptSegment.podcast_id == podcast_id).delete(synchronize_session=False)
        db.query(Chapter).filter(Chapter.podcast_id == podcast_id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not clear partial results for podcast %s", podcast_id)
    finally:
        db.close()


# ─── Main pipeline ────────────────────────────────────────────────────────────

def run_pipeline(job_id: str, podcast_id: str, audio_path: str):
    """
    Full AI processing pipeline executed in a background thread.
    Stages: preprocessing → transcribing → detecting_topics → generating_summaries → writing_metadata → completed
    """
    logger.info(f"[Job {job_id}] Pipeline started for podcast {podcast_id}")

    try:
        # ── 1. Preprocessing ──────────────────────────────────────────────────
        _update_job(job_id, "preprocessing", 0.05, "Inspecting audio file…")

        from app.services.audio import get_audio_info, validate_audio

        valid, err = validate_audio(audio_path)
        if not valid:
            raise ValueError(f"Invalid audio: {err}")

        info = get_audio_info(audio_path)
        duration = info["duration_seconds"]

        _update_podcast(
            podcast_id,
            duration_seconds=duration,
            channels=info["channels"],
            sample_rate=info["sample_rate"],
            audio_format=os.path.splitext(audio_path)[1].lstrip(".").upper(),
        )

        _update_job(job_id, "preprocessing", 0.10, f"Audio OK — {duration:.1f}s duration")

        # Whisper decodes source formats itself. Avoid a large temporary WAV
        # and an extra full-file decode for long recordings.
        _update_job(job_id, "preprocessing", 0.15, "Audio ready — starting fast transcription")

        # ── 2. Transcription ──────────────────────────────────────────────────
        _update_job(job_id, "transcribing", 0.20, "Preparing the fast CPU transcription model…")

        from app.services.transcription import transcribe_audio

        def whisper_progress(msg, pct):
            _update_job(job_id, "transcribing", 0.20 + pct * 0.35, msg)

        result = transcribe_audio(
            audio_path,
            model_name=settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            progress_callback=whisper_progress,
        )

        segments = result["segments"]
        full_text = result["text"]
        word_count = len(full_text.split())

        _update_podcast(podcast_id, word_count=word_count)
        _update_job(job_id, "transcribing", 0.55, f"Transcribed {word_count} words across {len(segments)} segments")

        # ── 3. Topic Detection ─────────────────────────────────────────────────
        _update_job(job_id, "detecting_topics", 0.58, "Running BERTopic topic detection…")

        from app.services.topic_detection import detect_topics, group_segments_into_chapters

        def topic_progress(msg, pct):
            _update_job(job_id, "detecting_topics", 0.58 + pct * 0.12, msg)

        enriched_segments, topic_labels = detect_topics(
            segments,
            embedding_model_name=settings.EMBEDDING_MODEL,
            progress_callback=topic_progress,
        )

        topic_count = len(set(s.get("topic_id", -1) for s in enriched_segments if s.get("topic_id", -1) != -1))
        _update_podcast(podcast_id, topic_count=topic_count)

        _update_job(job_id, "detecting_topics", 0.70, f"Detected {topic_count} topics")

        # Group into chapters
        raw_chapters = group_segments_into_chapters(
            enriched_segments,
            topic_labels,
            min_chapter_seconds=settings.MIN_CHAPTER_DURATION_SECONDS,
        )

        # ── 4. Summarization ──────────────────────────────────────────────────
        _update_job(job_id, "generating_summaries", 0.72, f"Generating summaries for {len(raw_chapters)} chapters…")

        from app.services.summarization import generate_all_chapter_summaries

        def summ_progress(msg, pct):
            _update_job(job_id, "generating_summaries", 0.72 + pct * 0.18, msg)

        chapters_with_summaries = generate_all_chapter_summaries(
            raw_chapters,
            model_name=settings.SUMMARIZER_MODEL,
            progress_callback=summ_progress,
        )

        _update_job(job_id, "generating_summaries", 0.90, "Summaries generated")

        # ── 5. Save to DB ──────────────────────────────────────────────────────
        _update_job(job_id, "writing_metadata", 0.92, "Saving results to database…")

        _save_segments(podcast_id, enriched_segments)
        _save_chapters(podcast_id, chapters_with_summaries)

        # ── 6. Generate exports ────────────────────────────────────────────────
        _update_job(job_id, "writing_metadata", 0.95, "Generating export files…")

        output_dir = os.path.join(settings.OUTPUT_DIR, podcast_id)
        os.makedirs(output_dir, exist_ok=True)

        # Load podcast info for exports
        db = SessionLocal()
        try:
            pod = db.query(Podcast).filter(Podcast.id == podcast_id).first()
            podcast_meta = {
                "id": pod.id,
                "title": pod.title,
                "artist": "Podcast Creator",
                "album": "Podcast Series",
                "year": str(datetime.now().year),
                "description": f"Podcast episode: {pod.title}",
                "duration_seconds": pod.duration_seconds,
                "word_count": pod.word_count,
            }
        finally:
            db.close()

        from app.services.export import (
            export_transcript_txt,
            export_chapters_markdown,
            export_full_analysis_json,
            export_tagged_mp3,
        )

        seg_dicts = [
            {
                "start_time": s["start"],
                "end_time": s["end"],
                "text": s["text"],
                "topic_label": s.get("topic_label"),
            }
            for s in enriched_segments
        ]
        ch_dicts = [
            {
                "chapter_number": c["chapter_number"],
                "title": c.get("title", f"Chapter {c['chapter_number']}"),
                "start_time": c["start_time"],
                "end_time": c["end_time"],
                "topic_label": c.get("topic_label"),
                "summary": c.get("summary"),
            }
            for c in chapters_with_summaries
        ]

        export_transcript_txt(seg_dicts, podcast_meta["title"], os.path.join(output_dir, "transcript.txt"))
        export_chapters_markdown(ch_dicts, podcast_meta["title"], os.path.join(output_dir, "chapters.md"))
        export_full_analysis_json(podcast_meta, seg_dicts, ch_dicts, os.path.join(output_dir, "analysis.json"))

        # Tagged MP3
        try:
            mp3_output = os.path.join(output_dir, "podcast_chapters.mp3")
            export_tagged_mp3(audio_path, podcast_meta, ch_dicts, mp3_output)
        except Exception as e:
            logger.warning(f"MP3 export failed (non-critical): {e}")

        # ── 7. Mark complete ───────────────────────────────────────────────────
        _update_podcast(podcast_id, status="completed", completed_at=datetime.now(timezone.utc))
        _update_job(job_id, "completed", 1.0, "Processing complete!")

        logger.info(f"[Job {job_id}] Pipeline completed successfully")

    except Exception as exc:
        logger.error(f"[Job {job_id}] Pipeline failed: {exc}", exc_info=True)
        _clear_partial_results(podcast_id)
        _update_job(job_id, "failed", 0.0, "Processing failed", error=str(exc))
        _update_podcast(podcast_id, status="failed", error_message=str(exc), word_count=None, topic_count=None)


def submit_job(job_id: str, podcast_id: str, audio_path: str):
    """Submit a processing job to the thread pool executor."""
    _executor.submit(run_pipeline, job_id, podcast_id, audio_path)
    logger.info(f"Job {job_id} submitted to executor")
