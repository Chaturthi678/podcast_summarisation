"""
ID3 metadata and chapter tagging service using Mutagen.
Writes CHAP frames to MP3 files.
"""
import json
import logging
import os
import struct
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def _ms(seconds: float) -> int:
    """Convert seconds to milliseconds (ID3 uses ms for chapter timestamps)."""
    return int(seconds * 1000)


def write_id3_chapters(
    mp3_path: str,
    podcast_title: str,
    artist: str,
    album: str,
    year: str,
    description: str,
    chapters: List[Dict[str, Any]],
) -> str:
    """
    Write ID3 tags and CHAP frames to an MP3 file.

    Args:
        mp3_path: Path to the MP3 file to tag.
        podcast_title: Podcast episode title.
        artist: Creator/host name.
        album: Podcast series name.
        year: Publication year.
        description: Episode description.
        chapters: List of {title, start_time, end_time, summary}.

    Returns:
        Path to the tagged MP3 file.
    """
    from mutagen.id3 import (
        ID3, TIT2, TPE1, TALB, TDRC, COMM, CTOC, CHAP,
        CTOCFlags, ID3NoHeaderError, TIT3,
    )
    from mutagen.mp3 import MP3

    # Load or create ID3 tags
    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        tags = ID3()

    # Clear existing chapter-related tags for clean write
    for key in list(tags.keys()):
        if key.startswith("CHAP") or key.startswith("CTOC"):
            del tags[key]

    # Standard tags
    tags.add(TIT2(encoding=3, text=podcast_title))
    tags.add(TPE1(encoding=3, text=artist))
    tags.add(TALB(encoding=3, text=album))
    tags.add(TDRC(encoding=3, text=year))
    tags.add(COMM(encoding=3, lang="eng", desc="", text=description))

    # Build chapter element IDs
    chapter_ids = [f"chp{i}" for i in range(len(chapters))]

    # CTOC (Table of Contents)
    tags.add(CTOC(
        encoding=3,
        element_id="toc",
        flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
        child_element_ids=chapter_ids,
        sub_frames=[TIT2(encoding=3, text="Table of Contents")],
    ))

    # Individual CHAP frames
    for i, (chap, elem_id) in enumerate(zip(chapters, chapter_ids)):
        start_ms = _ms(chap["start_time"])
        end_ms = _ms(chap["end_time"])

        tags.add(CHAP(
            encoding=3,
            element_id=elem_id,
            start_time=start_ms,
            end_time=end_ms,
            start_offset=0xFFFFFFFF,
            end_offset=0xFFFFFFFF,
            sub_frames=[
                TIT2(encoding=3, text=chap["title"]),
                TIT3(encoding=3, text=chap.get("summary", "")[:250]),
            ],
        ))

    tags.save(mp3_path, v2_version=3)
    logger.info(f"ID3 tags written to {mp3_path} ({len(chapters)} chapters)")
    return mp3_path


def read_id3_chapters(mp3_path: str) -> List[Dict[str, Any]]:
    """Read CHAP frames from an MP3 file (for verification)."""
    from mutagen.id3 import ID3, ID3NoHeaderError
    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        return []

    chapters = []
    for key, frame in tags.items():
        if key.startswith("CHAP"):
            title = ""
            summary = ""
            for sf in frame.sub_frames.values():
                if sf.FrameID == "TIT2":
                    title = str(sf)
                elif sf.FrameID == "TIT3":
                    summary = str(sf)
            chapters.append({
                "element_id": frame.element_id,
                "title": title,
                "summary": summary,
                "start_time_ms": frame.start_time,
                "end_time_ms": frame.end_time,
                "start_time_seconds": frame.start_time / 1000.0,
                "end_time_seconds": frame.end_time / 1000.0,
            })

    chapters.sort(key=lambda c: c["start_time_ms"])
    return chapters
