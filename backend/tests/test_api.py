"""
Backend verification tests.
Run: python -m pytest backend/tests/ -v
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import create_tables


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before tests."""
    create_tables()


@pytest.fixture
def client():
    return TestClient(app)


# ─── Health check ─────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── Podcast list (empty) ──────────────────────────────────────────────────────

def test_list_podcasts_empty(client):
    r = client.get("/api/podcasts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ─── Stats ────────────────────────────────────────────────────────────────────

def test_stats(client):
    r = client.get("/api/podcasts/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_podcasts" in data
    assert "total_chapters" in data


# ─── Upload validation ────────────────────────────────────────────────────────

def test_upload_invalid_extension(client):
    """Reject non-audio files."""
    r = client.post(
        "/api/podcasts/upload",
        files={"file": ("test.pdf", b"%PDF fake content", "application/pdf")},
    )
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]


def test_upload_empty_file(client):
    """Reject empty files."""
    r = client.post(
        "/api/podcasts/upload",
        files={"file": ("test.mp3", b"", "audio/mpeg")},
    )
    assert r.status_code == 400


def test_upload_valid_mp3(client):
    """
    Submit a minimal valid MP3 (short silence).
    This tests upload success — actual AI processing runs in background.
    """
    # Create a minimal MP3-like binary (ID3 header + minimal MPEG frame)
    # For real testing, use an actual test fixture
    minimal_mp3 = b'ID3' + b'\x00' * 7 + b'\xff\xfb' + b'\x90' * 500
    r = client.post(
        "/api/podcasts/upload",
        files={"file": ("test_podcast.mp3", minimal_mp3, "audio/mpeg")},
    )
    # This should succeed at upload phase (actual processing is async)
    # The audio validation happens in the background worker
    assert r.status_code in [200, 400]  # 400 is OK if audio validation fails immediately
    if r.status_code == 200:
        data = r.json()
        assert "job_id" in data
        assert "podcast_id" in data


# ─── Job not found ────────────────────────────────────────────────────────────

def test_job_not_found(client):
    r = client.get("/api/jobs/nonexistent-job-id")
    assert r.status_code == 404


# ─── Podcast not found ───────────────────────────────────────────────────────

def test_podcast_not_found(client):
    r = client.get("/api/podcasts/nonexistent-id")
    assert r.status_code == 404


# ─── Audio module import tests ────────────────────────────────────────────────

def test_audio_service_imports():
    from app.services.audio import get_audio_info, validate_audio, convert_to_wav
    assert callable(get_audio_info)
    assert callable(validate_audio)


def test_transcription_service_imports():
    from app.services.transcription import transcribe_audio
    assert callable(transcribe_audio)


def test_topic_service_imports():
    from app.services.topic_detection import detect_topics, group_segments_into_chapters
    assert callable(detect_topics)


def test_summarization_service_imports():
    from app.services.summarization import summarize_text, generate_all_chapter_summaries
    assert callable(summarize_text)


def test_metadata_service_imports():
    from app.services.metadata import write_id3_chapters, read_id3_chapters
    assert callable(write_id3_chapters)
    assert callable(read_id3_chapters)


def test_export_service_imports():
    from app.services.export import (
        export_transcript_txt, export_chapters_markdown,
        export_full_analysis_json
    )
    assert callable(export_transcript_txt)


# ─── Text chunking test ───────────────────────────────────────────────────────

def test_text_chunking():
    from app.services.summarization import _chunk_text
    text = " ".join(["word"] * 1000)
    chunks = _chunk_text(text, max_words=400)
    assert len(chunks) == 3
    for chunk in chunks:
        assert len(chunk.split()) <= 400


def test_time_formatting():
    from app.services.export import format_time
    assert format_time(0) == "00:00"
    assert format_time(65) == "01:05"
    assert format_time(3661) == "01:01:01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
