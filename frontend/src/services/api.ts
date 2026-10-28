import axios from 'axios';
import type {
  Podcast, PodcastListItem, Chapter, TranscriptSegment,
  UploadResponse, JobStatus, DashboardStats
} from '../types';

const api = axios.create({
  // In production, point this at the hosted FastAPI service (including /api).
  // Local development keeps using Vite's /api proxy by default.
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
});

export function getApiError(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (error.code === 'ECONNABORTED') return 'The request timed out. Please try again.';
    if (!error.response) return 'Could not reach Podly. Check that the backend is running.';
  }
  return error instanceof Error ? error.message : fallback;
}

export function friendlyProcessingError(error?: string | null): string {
  if (!error) return 'The audio could not be processed. Try a valid MP3, WAV, M4A, OGG, or FLAC file.';
  if (/WinError 2|ffprobe|ffmpeg version|Output from ffmpeg|Decoder requires|Could not find codec parameters/i.test(error)) {
    return 'A previous run could not start Whisper’s audio decoder. Podly now uses its bundled FFmpeg; retry this episode to continue.';
  }
  return error;
}

// ─── Podcasts ──────────────────────────────────────────────────────────────────

export async function uploadPodcast(file: File, onProgress?: (pct: number) => void): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<UploadResponse>('/podcasts/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return data;
}

export async function listPodcasts(limit = 50, offset = 0): Promise<PodcastListItem[]> {
  const { data } = await api.get<PodcastListItem[]>('/podcasts', { params: { limit, offset } });
  return data;
}

export async function getPodcast(id: string): Promise<Podcast> {
  const { data } = await api.get<Podcast>(`/podcasts/${id}`);
  return data;
}

export async function retryPodcast(id: string): Promise<JobStatus> {
  const { data } = await api.post<JobStatus>(`/podcasts/${id}/retry`);
  return data;
}

export async function getTranscript(id: string): Promise<TranscriptSegment[]> {
  const { data } = await api.get<TranscriptSegment[]>(`/podcasts/${id}/transcript`);
  return data;
}

export async function getChapters(id: string): Promise<Chapter[]> {
  const { data } = await api.get<Chapter[]>(`/podcasts/${id}/chapters`);
  return data;
}

export async function updateChapter(
  podcastId: string,
  chapterId: string,
  update: { title?: string; summary?: string }
): Promise<Chapter> {
  const { data } = await api.patch<Chapter>(`/podcasts/${podcastId}/chapters/${chapterId}`, update);
  return data;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/podcasts/stats');
  return data;
}

export function getAudioUrl(podcastId: string): string {
  return api.getUri({ url: `/podcasts/${podcastId}/audio` });
}

export function getDownloadUrl(podcastId: string, format: 'txt' | 'md' | 'json' | 'mp3'): string {
  return api.getUri({ url: `/podcasts/${podcastId}/download/${format}` });
}

export async function downloadExport(podcastId: string, format: 'txt' | 'md' | 'json' | 'mp3'): Promise<Blob> {
  const { data } = await api.get<Blob>(`/podcasts/${podcastId}/download/${format}`, { responseType: 'blob' });
  return data;
}

// ─── Jobs ──────────────────────────────────────────────────────────────────────

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const { data } = await api.get<JobStatus>(`/jobs/${jobId}`);
  return data;
}

export async function checkHealth(): Promise<boolean> {
  try {
    await api.get('/health');
    return true;
  } catch {
    return false;
  }
}
