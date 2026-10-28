"""
Real Whisper ASR transcription service.
Uses openai-whisper. Model is loaded once and cached in memory.
"""
import logging
import os
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Module-level model cache
_whisper_model = None
_loaded_model_name: Optional[str] = None
_faster_whisper_model = None
_loaded_faster_key: Optional[tuple] = None
_whisper_ffmpeg_patched = False
_model_load_lock = threading.Lock()


def _selected_model_name(model_name: str) -> str:
    from app.config import settings
    caches = [Path(settings.MODEL_CACHE_DIR), Path.home() / ".cache" / "whisper"]
    tiny_cached = any((cache / "tiny.pt").is_file() for cache in caches)
    base_cached = any((cache / "base.pt").is_file() for cache in caches)
    if model_name == "tiny" and not tiny_cached and base_cached:
        return "base"
    return model_name


def _configure_whisper_ffmpeg(whisper):
    """Make Whisper use imageio-ffmpeg's bundled binary on Windows."""
    global _whisper_ffmpeg_patched
    if _whisper_ffmpeg_patched:
        return
    import whisper.audio as whisper_audio
    from app.services.audio import _ffmpeg_path

    original_run = whisper_audio.run

    def run_with_bundled_ffmpeg(command, *args, **kwargs):
        command = list(command)
        if command and os.path.basename(str(command[0])).lower().startswith("ffmpeg"):
            command[0] = _ffmpeg_path()
        return original_run(command, *args, **kwargs)

    whisper_audio.run = run_with_bundled_ffmpeg
    _whisper_ffmpeg_patched = True


def load_whisper_model(model_name: str = "base", device: str = "cpu"):
    """Load Whisper model into memory (cached after first load)."""
    global _whisper_model, _loaded_model_name

    selected_model = _selected_model_name(model_name)
    with _model_load_lock:
        if _whisper_model is not None and _loaded_model_name == selected_model:
            logger.info(f"Using cached Whisper model: {selected_model}")
            return _whisper_model

        try:
            import whisper
            _configure_whisper_ffmpeg(whisper)
            # Prefer the fast model, but don't force a network download when a
            # cached base model is already available offline.
            if selected_model != model_name:
                logger.info("Tiny Whisper weights are not cached; using the available base model")
            logger.info(f"Loading Whisper model '{selected_model}' on {device}…")
            from app.config import settings
            _whisper_model = whisper.load_model(selected_model, device=device, download_root=settings.MODEL_CACHE_DIR)
            _loaded_model_name = selected_model
            logger.info(f"Whisper model '{selected_model}' loaded successfully")
            return _whisper_model
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Whisper model load failed: {e}") from e


def load_faster_whisper_model(model_name: str = "tiny", device: str = "cpu"):
    """Load a cached CTranslate2 Whisper model, using int8 on CPU."""
    global _faster_whisper_model, _loaded_faster_key

    from app.config import settings

    compute_type = "int8" if device == "cpu" else "float16"
    cache_key = (model_name, device, compute_type)
    with _model_load_lock:
        if _faster_whisper_model is not None and _loaded_faster_key == cache_key:
            return _faster_whisper_model

        try:
            import av
            from faster_whisper import WhisperModel
            import faster_whisper.audio as faster_audio

            # Keep av pinned below 19 in requirements: faster-whisper 1.2.1
            # still passes metadata_errors to av.open, which PyAV 19 removed.
            if int(av.__version__.split(".", 1)[0]) >= 19 and not getattr(
                faster_audio, "_podly_pyav19_compat", False
            ):
                original_open = av.open

                def open_without_removed_metadata_option(*args, **kwargs):
                    kwargs.pop("metadata_errors", None)
                    return original_open(*args, **kwargs)

                faster_audio.av.open = open_without_removed_metadata_option
                faster_audio._podly_pyav19_compat = True

            logger.info(
                "Loading faster-whisper model '%s' on %s (%s)",
                model_name,
                device,
                compute_type,
            )
            _faster_whisper_model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=settings.MODEL_CACHE_DIR,
            )
            _loaded_faster_key = cache_key
            logger.info("faster-whisper model '%s' loaded successfully", model_name)
            return _faster_whisper_model
        except Exception as e:
            logger.error("Failed to load faster-whisper model: %s", e)
            raise RuntimeError(f"Faster Whisper model load failed: {e}") from e


def transcribe_audio(
    audio_path: str,
    model_name: str = "base",
    device: str = "cpu",
    language: Optional[str] = None,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Transcribe audio using Whisper.
    Returns dict with 'text', 'segments', 'language'.
    Each segment: {id, start, end, text, ...}
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    logger.info(f"Starting transcription of: {audio_path}")
    if progress_callback:
        progress_callback("Preparing the transcription model…", 0.02)

    try:
        from app.config import settings

        engine = settings.TRANSCRIPTION_ENGINE.strip().lower()
        segments = []
        if engine == "faster-whisper":
            try:
                model = load_faster_whisper_model(model_name, device)
            except RuntimeError as exc:
                logger.warning("faster-whisper unavailable; using OpenAI Whisper fallback: %s", exc)
                if progress_callback:
                    progress_callback("Fast model unavailable; switching to Whisper fallback…", 0.02)
                engine = "openai-whisper"

        if engine == "faster-whisper":
            segment_iter, info = model.transcribe(
                audio_path,
                language=language,
                beam_size=1,
                best_of=1,
                word_timestamps=False,
                condition_on_previous_text=False,
                vad_filter=False,
            )
            duration = max(float(getattr(info, "duration", 0) or 0), 1.0)
            last_reported_at = time.monotonic()
            for i, seg in enumerate(segment_iter):
                text = seg.text.strip()
                if text:
                    segments.append({
                        "id": i,
                        "start": float(seg.start),
                        "end": float(seg.end),
                        "text": text,
                        "words": [],
                    })
                pct = min(float(seg.end) / duration, 0.99)
                now = time.monotonic()
                if progress_callback and (now - last_reported_at >= 2):
                    progress_callback(
                        f"Transcribing audio… {round(pct * 100)}% of the recording",
                        pct,
                    )
                    last_reported_at = now
            detected_language = getattr(info, "language", None) or language or "unknown"
        else:
            model = load_whisper_model(model_name, device)
            import whisper

            options: Dict[str, Any] = {
                "verbose": False,
                "word_timestamps": False,
                "fp16": False,
                "beam_size": 1,
                "best_of": 1,
                "condition_on_previous_text": False,
            }
            if language:
                options["language"] = language
            result = model.transcribe(audio_path, **options)
            segments = [
                {
                    "id": i,
                    "start": float(seg["start"]),
                    "end": float(seg["end"]),
                    "text": seg["text"].strip(),
                    "words": seg.get("words", []),
                }
                for i, seg in enumerate(result.get("segments", []))
            ]
            detected_language = result.get("language", "unknown")

        full_text = " ".join(seg["text"] for seg in segments)
        logger.info(
            "Transcription done: %s segments, language=%s, engine=%s",
            len(segments),
            detected_language,
            engine,
        )

        if progress_callback:
            progress_callback("Transcription complete", 1.0)

        return {
            "text": full_text.strip(),
            "segments": segments,
            "language": detected_language,
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Whisper transcription failed: {e}") from e
