"""
Export service: generates TXT, Markdown, JSON, and tagged MP3 exports.
"""
import json
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def export_transcript_txt(
    segments: List[Dict[str, Any]],
    podcast_title: str,
    output_path: str,
) -> str:
    """Export transcript as plain text with timestamps."""
    lines = [f"TRANSCRIPT: {podcast_title}", "=" * 60, ""]
    for seg in segments:
        ts = format_time(seg["start_time"])
        lines.append(f"[{ts}] {seg['text']}")
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"TXT transcript exported: {output_path}")
    return output_path


def export_chapters_markdown(
    chapters: List[Dict[str, Any]],
    podcast_title: str,
    output_path: str,
) -> str:
    """Export chapter summaries as Markdown."""
    lines = [f"# {podcast_title} — Chapter Summaries", ""]
    for ch in chapters:
        start = format_time(ch["start_time"])
        end = format_time(ch["end_time"])
        lines += [
            f"## Chapter {ch['chapter_number']}: {ch['title']}",
            f"**Timestamps:** {start} → {end}",
            f"**Topic:** {ch.get('topic_label', 'Unknown')}",
            "",
            ch.get("summary", ""),
            "",
            "---",
            "",
        ]
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Markdown chapters exported: {output_path}")
    return output_path


def export_full_analysis_json(
    podcast_meta: Dict[str, Any],
    segments: List[Dict[str, Any]],
    chapters: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """Export full analysis as structured JSON."""
    data = {
        "podcast": podcast_meta,
        "chapters": chapters,
        "transcript": segments,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"JSON analysis exported: {output_path}")
    return output_path


def export_tagged_mp3(
    original_audio_path: str,
    podcast_meta: Dict[str, Any],
    chapters: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """
    Create a tagged MP3 with ID3 chapter frames.
    Converts to MP3 first if the source is WAV/M4A.
    """
    from app.services.audio import convert_to_mp3
    from app.services.metadata import write_id3_chapters

    ext = os.path.splitext(original_audio_path)[1].lower()

    # Convert to MP3 if necessary
    if ext != ".mp3":
        mp3_intermediate = output_path.replace(".mp3", "_raw.mp3")
        logger.info(f"Converting {ext} to MP3 for ID3 tagging")
        convert_to_mp3(original_audio_path, mp3_intermediate)
        source_mp3 = mp3_intermediate
    else:
        import shutil
        source_mp3 = output_path + ".src.mp3"
        shutil.copy2(original_audio_path, source_mp3)

    # Copy to output path then tag in-place
    import shutil
    shutil.copy2(source_mp3, output_path)

    write_id3_chapters(
        mp3_path=output_path,
        podcast_title=podcast_meta.get("title", "Untitled"),
        artist=podcast_meta.get("artist", "Unknown"),
        album=podcast_meta.get("album", "Podcast"),
        year=podcast_meta.get("year", "2024"),
        description=podcast_meta.get("description", ""),
        chapters=[
            {
                "title": ch["title"],
                "start_time": ch["start_time"],
                "end_time": ch["end_time"],
                "summary": ch.get("summary", ""),
            }
            for ch in chapters
        ],
    )

    # Cleanup intermediate file
    if ext != ".mp3" and os.path.exists(source_mp3):
        os.remove(source_mp3)

    logger.info(f"Tagged MP3 exported: {output_path}")
    return output_path
