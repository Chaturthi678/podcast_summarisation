// ── Podcast & Job types ──────────────────────────────────────────────────────

export interface JobStatus {
  id: string;
  podcast_id: string | null;
  stage: string;
  progress: number;
  message: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranscriptSegment {
  id: string;
  podcast_id: string;
  segment_index: number;
  start_time: number;
  end_time: number;
  text: string;
  topic_id: number | null;
  topic_label: string | null;
  confidence: number | null;
}

export interface Chapter {
  id: string;
  podcast_id: string;
  chapter_number: number;
  title: string;
  start_time: number;
  end_time: number;
  topic_id: number | null;
  topic_label: string | null;
  topic_keywords: string | null;
  summary: string | null;
  segment_ids: string | null;
  is_edited: boolean;
}

export interface Podcast {
  id: string;
  job_id: string;
  title: string;
  filename: string;
  original_filename: string;
  file_size_bytes: number | null;
  duration_seconds: number | null;
  audio_format: string | null;
  sample_rate: number | null;
  channels: number | null;
  word_count: number | null;
  topic_count: number | null;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface PodcastListItem {
  id: string;
  job_id: string;
  title: string;
  original_filename: string;
  duration_seconds: number | null;
  word_count: number | null;
  topic_count: number | null;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export interface UploadResponse {
  job_id: string;
  podcast_id: string;
  message: string;
}

export interface DashboardStats {
  total_podcasts: number;
  completed_podcasts: number;
  total_duration_seconds: number;
  total_chapters: number;
  total_words: number;
}

// Processing stages
export const PROCESSING_STAGES = [
  { key: 'queued',               label: 'Queued',                   step: 0 },
  { key: 'preprocessing',        label: 'Preprocessing Audio',       step: 1 },
  { key: 'transcribing',         label: 'Transcribing with Whisper', step: 2 },
  { key: 'detecting_topics',     label: 'Grouping Topics (fast mode)',step: 3 },
  { key: 'generating_summaries', label: 'Writing Chapter Highlights',step: 4 },
  { key: 'writing_metadata',     label: 'Writing Chapter Metadata',  step: 5 },
  { key: 'completed',            label: 'Complete',                  step: 6 },
  { key: 'failed',               label: 'Failed',                    step: -1 },
];
