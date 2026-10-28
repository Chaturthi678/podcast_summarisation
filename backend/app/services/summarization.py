"""
NLP Summarization service using HuggingFace Transformers.
Uses DistilBART by default — fast enough for CPU.
"""
import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Module-level model cache
_summarizer = None
_loaded_summarizer_model: Optional[str] = None


def load_summarizer(model_name: str = "sshleifer/distilbart-cnn-12-6"):
    """Load the summarization pipeline (cached)."""
    global _summarizer, _loaded_summarizer_model

    if _summarizer is not None and _loaded_summarizer_model == model_name:
        return _summarizer

    logger.info(f"Loading summarization model: {model_name}")
    try:
        from transformers import pipeline
        _summarizer = pipeline(
            "summarization",
            model=model_name,
            device=-1,      # CPU
            truncation=True,
        )
        _loaded_summarizer_model = model_name
        logger.info(f"Summarizer loaded: {model_name}")
        return _summarizer
    except Exception as e:
        logger.error(f"Failed to load summarizer: {e}")
        raise RuntimeError(f"Summarizer load failed: {e}") from e


def _chunk_text(text: str, max_words: int = 400) -> List[str]:
    """Split text into chunks of at most max_words words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i : i + max_words]))
    return chunks


def _extractive_summary(text: str, max_words: int = 65) -> str:
    """Create a fast, readable chapter highlight without downloading a model."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    chosen = []
    for sentence in sorted(sentences, key=lambda item: (len(item.split()) >= 5, len(item.split())), reverse=True):
        if len(" ".join(chosen + [sentence]).split()) > max_words:
            continue
        chosen.append(sentence)
        if len(chosen) >= 2:
            break
    if chosen:
        return " ".join(chosen)
    words = text.split()
    return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


def summarize_text(
    text: str,
    model_name: str = "sshleifer/distilbart-cnn-12-6",
    max_length: int = 150,
    min_length: int = 30,
) -> str:
    """
    Summarize a block of text. Handles chunking for long inputs.
    Returns a summary string.
    """
    if not text or len(text.split()) < 10:
        return text.strip() if text else "No content available."

    from app.config import settings
    if settings.FAST_PROCESSING:
        return _extractive_summary(text)

    try:
        summarizer = load_summarizer(model_name)
        # Chunk if text is very long
        chunks = _chunk_text(text, max_words=400)

        if len(chunks) == 1:
            result = summarizer(
                chunks[0],
                max_length=max_length,
                min_length=min(min_length, max(5, len(chunks[0].split()) // 3)),
                do_sample=False,
            )
            return result[0]["summary_text"].strip()
        else:
            # Summarize each chunk then combine
            summaries = []
            for chunk in chunks:
                r = summarizer(
                    chunk,
                    max_length=100,
                    min_length=20,
                    do_sample=False,
                )
                summaries.append(r[0]["summary_text"].strip())
            combined = " ".join(summaries)

            # If combined is still long, summarize again
            if len(combined.split()) > 200:
                final = summarizer(
                    combined,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                )
                return final[0]["summary_text"].strip()
            return combined

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        # Return a truncated excerpt as fallback
        words = text.split()
        return " ".join(words[:80]) + "…" if len(words) > 80 else text


def generate_chapter_title(text: str, topic_label: str) -> str:
    """
    Generate a short chapter title.
    First tries to use the topic label, then cleans it up.
    Falls back to extracting key phrases from text.
    """
    if topic_label and topic_label not in ("Miscellaneous", "Unknown", "-1"):
        # Clean up BERTopic label (comma-separated keywords)
        parts = [p.strip().title() for p in topic_label.split(",")]
        if len(parts) >= 2:
            return f"{parts[0]} & {parts[1]}"
        return parts[0]

    # Simple title extraction: first non-trivial sentence
    sentences = text.replace("\n", " ").split(".")
    for sent in sentences:
        words = sent.strip().split()
        if 4 <= len(words) <= 12:
            return sent.strip().title()

    return "Chapter Overview"


def generate_all_chapter_summaries(
    chapters: List[Dict[str, Any]],
    model_name: str = "sshleifer/distilbart-cnn-12-6",
    progress_callback=None,
) -> List[Dict[str, Any]]:
    """
    Generate titles and summaries for all chapters.
    Returns list of chapters with 'title' and 'summary' fields added.
    """
    total = len(chapters)
    enriched = []

    for i, chapter in enumerate(chapters):
        text = chapter.get("text", "")
        topic_label = chapter.get("topic_label", "")

        logger.info(f"Summarizing chapter {i + 1}/{total}")

        if progress_callback:
            pct = i / total
            progress_callback(f"Generating summary for chapter {i + 1}/{total}…", pct)

        title = generate_chapter_title(text, topic_label)
        summary = summarize_text(text, model_name=model_name)

        enriched.append({
            **chapter,
            "title": title,
            "summary": summary,
        })

    return enriched
