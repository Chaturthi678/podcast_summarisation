"""
BERTopic topic detection service.
Groups transcript segments into topics and maps topics to chapters.
"""
import logging
import json
import re
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Module-level BERTopic cache
_topic_model = None


def _build_topic_model(embedding_model_name: str = "all-MiniLM-L6-v2"):
    """Build a BERTopic model optimized for podcast transcripts."""
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP
    from hdbscan import HDBSCAN

    sentence_model = SentenceTransformer(embedding_model_name)

    umap_model = UMAP(
        n_neighbors=5,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )

    vectorizer_model = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
    )

    topic_model = BERTopic(
        embedding_model=sentence_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        top_n_words=10,
        calculate_probabilities=True,
        verbose=False,
    )
    return topic_model


def detect_topics(
    segments: List[Dict[str, Any]],
    embedding_model_name: str = "all-MiniLM-L6-v2",
    min_topic_size: int = 2,
    progress_callback=None,
) -> Tuple[List[Dict[str, Any]], Dict[int, str]]:
    """
    Run BERTopic on transcript segments.

    Args:
        segments: List of {start, end, text, ...}
        embedding_model_name: SentenceTransformer model name
        min_topic_size: Minimum docs per topic
        progress_callback: Optional callback(message, progress)

    Returns:
        (enriched_segments, topic_labels_dict)
        enriched_segments: each segment with 'topic_id' and 'topic_label' added
        topic_labels_dict: {topic_id: label_string}
    """
    if not segments:
        return segments, {}

    from app.config import settings
    if settings.FAST_PROCESSING:
        if progress_callback:
            progress_callback("Grouping transcript into fast topic sections…", 0.8)
        return _fallback_topic_assignment(segments)

    texts = [seg["text"].strip() for seg in segments]

    # Filter out empty texts
    valid_indices = [i for i, t in enumerate(texts) if len(t.split()) >= 3]
    valid_texts = [texts[i] for i in valid_indices]

    if len(valid_texts) < 2:
        logger.warning("Not enough text for BERTopic — assigning single topic")
        enriched = []
        for seg in segments:
            enriched.append({**seg, "topic_id": 0, "topic_label": "Main Topic"})
        return enriched, {0: "Main Topic"}

    if progress_callback:
        progress_callback("Building topic model with BERTopic…", 0.2)

    logger.info(f"Running BERTopic on {len(valid_texts)} segments")
    try:
        topic_model = _build_topic_model(embedding_model_name)
        topics, probabilities = topic_model.fit_transform(valid_texts)

        # Build label map
        topic_info = topic_model.get_topic_info()
        topic_labels: Dict[int, str] = {}
        for _, row in topic_info.iterrows():
            tid = int(row["Topic"])
            if tid == -1:
                topic_labels[-1] = "Miscellaneous"
            else:
                # Build label from top keywords
                words = topic_model.get_topic(tid)
                if words:
                    label = ", ".join([w for w, _ in words[:3]])
                    topic_labels[tid] = label.title()
                else:
                    topic_labels[tid] = f"Topic {tid + 1}"

        if progress_callback:
            progress_callback("Topic detection complete", 0.8)

        # Map topics back to all segments
        topic_map = {}
        for rank, idx in enumerate(valid_indices):
            topic_map[idx] = int(topics[rank])

        enriched = []
        for i, seg in enumerate(segments):
            tid = topic_map.get(i, -1)
            label = topic_labels.get(tid, "Miscellaneous")
            enriched.append({
                **seg,
                "topic_id": tid,
                "topic_label": label,
            })

        unique_topics = set(t for t in topics if t != -1)
        logger.info(f"BERTopic found {len(unique_topics)} topics")
        return enriched, topic_labels

    except Exception as e:
        logger.error(f"BERTopic failed: {e}")
        # Graceful fallback: assign topics based on time quartiles
        logger.warning("Falling back to time-based topic assignment")
        return _fallback_topic_assignment(segments)


def _fallback_topic_assignment(
    segments: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[int, str]]:
    """Fallback: divide into time-based groups when BERTopic can't cluster."""
    if not segments:
        return segments, {}

    total_dur = max(seg["end"] for seg in segments) if segments else 1
    n_groups = max(2, min(4, len(segments) // 3))
    group_dur = total_dur / n_groups

    enriched = []
    for seg in segments:
        group = min(int(seg["start"] / group_dur), n_groups - 1)
        enriched.append({**seg, "topic_id": group})

    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    stopwords = set(ENGLISH_STOP_WORDS) | {"yeah", "yes", "okay", "right", "really", "thing", "things", "think", "today", "welcome", "sample", "episode", "chapter", "listen", "listening", "topic", "topics", "conversation", "idea", "ideas", "section", "sections", "podly", "gonna", "gotta", "wanna", "uh", "um"}
    labels = {}
    for group in range(n_groups):
        words = Counter(
            word for seg in enriched if seg["topic_id"] == group
            for raw_word in re.findall(r"[a-z][a-z'-]{2,}", seg["text"].lower())
            for word in [raw_word.replace("'", "").replace("-", "")]
            if word not in stopwords and len(word) >= 4
        )
        keywords = [word.title() for word, _ in words.most_common(2)]
        labels[group] = " & ".join(keywords) if keywords else f"Topic {group + 1}"

    enriched = [{**seg, "topic_label": labels[seg["topic_id"]]} for seg in enriched]

    return enriched, labels


def group_segments_into_chapters(
    segments: List[Dict[str, Any]],
    topic_labels: Dict[int, str],
    min_chapter_seconds: int = 30,
) -> List[Dict[str, Any]]:
    """
    Group consecutive segments with the same topic into chapter candidates.
    Merges very short chapters with adjacent ones.
    """
    if not segments:
        return []

    chapters = []
    current_topic = segments[0]["topic_id"]
    current_label = segments[0]["topic_label"]
    current_start = segments[0]["start"]
    current_end = segments[0]["end"]
    current_segs = [segments[0]]

    for seg in segments[1:]:
        if seg["topic_id"] == current_topic:
            current_end = seg["end"]
            current_segs.append(seg)
        else:
            chapters.append({
                "topic_id": current_topic,
                "topic_label": current_label,
                "start_time": current_start,
                "end_time": current_end,
                "segments": current_segs,
                "text": " ".join(s["text"] for s in current_segs),
            })
            current_topic = seg["topic_id"]
            current_label = seg["topic_label"]
            current_start = seg["start"]
            current_end = seg["end"]
            current_segs = [seg]

    # Append last group
    chapters.append({
        "topic_id": current_topic,
        "topic_label": current_label,
        "start_time": current_start,
        "end_time": current_end,
        "segments": current_segs,
        "text": " ".join(s["text"] for s in current_segs),
    })

    # Merge chapters shorter than min_chapter_seconds with neighbours
    merged = []
    for ch in chapters:
        dur = ch["end_time"] - ch["start_time"]
        if dur < min_chapter_seconds and merged:
            # Merge into previous chapter
            prev = merged[-1]
            prev["end_time"] = ch["end_time"]
            prev["segments"].extend(ch["segments"])
            prev["text"] += " " + ch["text"]
        else:
            merged.append(ch)

    # Number chapters
    for i, ch in enumerate(merged):
        ch["chapter_number"] = i + 1

    return merged
