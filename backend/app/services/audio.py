"""Audio inspection and conversion helpers using Mutagen and bundled FFmpeg."""
import logging
import os
import subprocess
from typing import Tuple

logger = logging.getLogger(__name__)


def _ffmpeg_path() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        logger.exception("Could not locate bundled FFmpeg")
        raise RuntimeError("FFmpeg is unavailable. Install imageio-ffmpeg and try again.") from exc


def get_audio_info(file_path: str) -> dict:
    """Read audio metadata without decoding the complete recording."""
    if not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
        raise ValueError("The audio file is missing or empty.")
    try:
        from mutagen import File as MutagenFile
        media = MutagenFile(file_path)
        info = getattr(media, "info", None)
        if info is None:
            raise ValueError("No audio stream was found.")
        duration = float(getattr(info, "length", 0) or 0)
        sample_rate = int(getattr(info, "sample_rate", 0) or 0)
        channels = int(getattr(info, "channels", 0) or 0)
        if duration <= 0:
            raise ValueError("No playable audio stream was found.")
        return {
            "duration_seconds": duration,
            "channels": channels or 1,
            "sample_rate": sample_rate,
            "frame_count": round(duration * sample_rate) if sample_rate else 0,
            "sample_width": max(1, int(getattr(info, "bits_per_sample", 16) or 16) // 8),
        }
    except Exception as exc:
        logger.info("Audio metadata could not be read for %s: %s", file_path, exc)
        raise ValueError("The audio file could not be read. It may be incomplete, corrupted, or missing an audio track.") from exc


def _convert(args: list[str], message: str) -> None:
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logger.warning("%s: %s", message, result.stderr[-1200:])
            raise ValueError(message)
    except OSError as exc:
        logger.exception("FFmpeg could not start")
        raise ValueError("FFmpeg could not start. Please restart the backend and try again.") from exc


def convert_to_wav(input_path: str, output_path: str) -> str:
    """Stream-convert audio to 16 kHz mono PCM for Whisper."""
    _convert([
        _ffmpeg_path(), "-y", "-i", input_path, "-vn", "-ac", "1",
        "-ar", "16000", "-c:a", "pcm_s16le", output_path,
    ], "The audio file could not be converted. Please upload a valid audio file.")
    return output_path


def convert_to_mp3(input_path: str, output_path: str) -> str:
    """Stream-convert audio to a tagged-audio compatible MP3."""
    _convert([
        _ffmpeg_path(), "-y", "-i", input_path, "-vn", "-c:a", "libmp3lame",
        "-b:a", "192k", output_path,
    ], "The audio file could not be converted to MP3.")
    return output_path


def validate_audio(file_path: str) -> Tuple[bool, str]:
    """Check that a non-empty audio file contains at least one second of audio."""
    if not os.path.exists(file_path):
        return False, "Audio file not found."
    if os.path.getsize(file_path) == 0:
        return False, "Audio file is empty."
    try:
        info = get_audio_info(file_path)
        duration = info.get("duration_seconds", 0)
        if duration < 1.0:
            return False, "Audio is too short. Please upload at least one second of audio."
        return True, ""
    except Exception as exc:
        return False, str(exc)
