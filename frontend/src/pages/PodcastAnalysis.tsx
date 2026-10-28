import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, Mic2, FileText, BookOpen, Clock, Download, Loader2,
  Sparkles, Headphones, CircleHelp, AlertTriangle
} from 'lucide-react';
import { getApiError, friendlyProcessingError, getPodcast, getTranscript, getChapters, getAudioUrl, retryPodcast } from '../services/api';
import type { Podcast, TranscriptSegment, Chapter } from '../types';
import { AudioPlayer } from '../components/Player/AudioPlayer';
import { ChapterCard } from '../components/Chapters/ChapterCard';
import { TranscriptExplorer } from '../components/Transcript/TranscriptExplorer';
import { ExportPanel } from '../components/Export/ExportPanel';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import { useJobPoller } from '../hooks/useJobPoller';
import { ProcessingStatus } from '../components/Upload/ProcessingStatus';
import toast from 'react-hot-toast';

function fmtDur(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${s}s`;
}

type Tab = 'overview' | 'chapters' | 'transcript' | 'export';

export function PodcastAnalysis() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [podcast, setPodcast] = useState<Podcast | null>(null);
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [loadedTranscriptPodcastId, setLoadedTranscriptPodcastId] = useState<string | null>(null);
  const [transcriptErrorState, setTranscriptErrorState] = useState<{ podcastId: string; message: string } | null>(null);
  const [transcriptRetry, setTranscriptRetry] = useState(0);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [tab, setTab] = useState<Tab>(() => {
    const requested = searchParams.get('tab');
    return requested === 'chapters' || requested === 'transcript' || requested === 'export' ? requested : 'overview';
  });
  const [retryJobId, setRetryJobId] = useState<string | null>(null);
  const [retryStarting, setRetryStarting] = useState(false);
  const { job: retryJob, error: retryError } = useJobPoller(retryJobId);
  const segmentsLoaded = loadedTranscriptPodcastId === id;
  const transcriptError = transcriptErrorState && transcriptErrorState.podcastId === id ? transcriptErrorState.message : '';

  const { state: playerState, togglePlay, seekTo, setVolume, setRate } = useAudioPlayer(
    id ? getAudioUrl(id) : null
  );

  useEffect(() => {
    if (!id) return;
    let active = true;
    Promise.all([getPodcast(id), getChapters(id)])
      .then(([pod, chs]) => {
        if (!active) return;
        setPodcast(pod);
        setChapters(chs);
      })
      .catch(err => { if (active) setLoadError(getApiError(err, 'Could not load this episode.')); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id, navigate]);

  useEffect(() => {
    if (!id || tab !== 'transcript' || segmentsLoaded) return;
    let active = true;
    getTranscript(id)
      .then(items => {
        if (!active) return;
        setSegments(items);
        setLoadedTranscriptPodcastId(id);
      })
      .catch(error => {
        if (active) setTranscriptErrorState({ podcastId: id, message: getApiError(error, 'Could not load the transcript.') });
      });
    return () => { active = false; };
  }, [id, tab, segmentsLoaded, transcriptRetry]);

  const retryStage = retryJob?.stage;
  const retryFailure = retryJob?.error;
  const retrying = retryStarting || Boolean(retryJobId && retryStage !== 'failed' && retryStage !== 'completed');

  useEffect(() => {
    if (!id || !retryStage) return;
    if (retryStage === 'completed') {
      Promise.all([getPodcast(id), getChapters(id)]).then(([pod, chs]) => {
        setPodcast(pod); setChapters(chs); setSegments([]); setLoadedTranscriptPodcastId(null); setTranscriptErrorState(null); setRetryJobId(null); toast.success('Episode analysis complete');
      }).catch(error => toast.error(getApiError(error)));
    }
  }, [id, retryStage, retryFailure]);

  const handleRetry = async () => {
    if (!id) return;
    setRetryStarting(true);
    try {
      const job = await retryPodcast(id);
      setRetryStarting(false);
      setSegments([]); setLoadedTranscriptPodcastId(null); setTranscriptErrorState(null);
      setPodcast(current => current ? { ...current, status: 'pending', error_message: null } : current);
      setRetryJobId(job.id);
      toast.success('Retry started. This can take a few minutes.');
    } catch (error) {
      setRetryStarting(false);
      toast.error(getApiError(error, 'Could not retry this episode.'));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="animate-spin" style={{ color: 'var(--accent-purple)' }} />
      </div>
    );
  }

  if (!podcast) return <div className="surface-card mx-auto mt-8 max-w-xl rounded-2xl p-7 text-center"><h1 className="text-lg font-semibold">Episode unavailable</h1><p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>{loadError || 'This episode could not be found.'}</p><button onClick={() => navigate('/podcasts')} className="mt-5 rounded-xl px-4 py-2.5 text-sm font-semibold text-white" style={{ background: 'var(--gradient-primary)' }}>Back to library</button></div>;

  const episodeFailed = podcast.status === 'failed' || retryStage === 'failed';

  const episodeBrief = chapters
    .map(ch => ch.summary?.trim())
    .filter((summary): summary is string => Boolean(summary))
    .slice(0, 3);
  const speechRate = podcast.duration_seconds && podcast.duration_seconds >= 60 && podcast.word_count != null
    ? Math.round(podcast.word_count / (podcast.duration_seconds / 60))
    : null;
  const lowTranscriptCoverage = speechRate !== null && speechRate < 30;

  const tabs: { key: Tab; label: string; icon: typeof Mic2 }[] = [
    { key: 'overview',    label: 'Brief',      icon: Sparkles },
    { key: 'chapters',    label: 'Chapters',   icon: BookOpen },
    { key: 'transcript',  label: 'Transcript', icon: FileText },
    { key: 'export',      label: 'Export',     icon: Download },
  ];

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Back + title */}
      <div className="flex items-start gap-4">
        <button onClick={() => navigate('/podcasts')}
          className="flex items-center gap-2 text-sm mt-1 transition-colors hover:opacity-70"
          style={{ color: 'var(--text-secondary)' }}>
          <ArrowLeft size={15} />
          Back
        </button>
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            {podcast.title}
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            {podcast.original_filename}
          </p>
        </div>
      </div>

      {episodeFailed && (
        <div className="rounded-2xl border p-4" style={{ background: '#fff6f2', borderColor: '#f2d9d0' }}>
          <p className="text-sm font-semibold" style={{ color: '#994b3c' }}>This episode could not be processed</p>
          <p className="mt-1 break-words text-sm" style={{ color: '#8b6259' }}>{friendlyProcessingError(retryStage === 'failed' ? retryFailure : podcast.error_message)}</p>
          <div className="mt-3 flex flex-wrap gap-2"><button onClick={handleRetry} disabled={retrying} className="rounded-lg px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" style={{ background: '#397e68' }}>{retrying ? 'Retrying…' : 'Retry analysis'}</button><button onClick={() => navigate('/upload')} className="rounded-lg border px-3 py-2 text-xs font-semibold" style={{ borderColor: '#e6c9bf', color: '#8b6259' }}>Upload another audio file</button></div>
        </div>
      )}

      {retryJob && retryStage !== 'failed' && <ProcessingStatus job={retryJob} filename={podcast.original_filename} connectionError={retryError} />}

      {/* Audio player */}
      {!episodeFailed && <AudioPlayer
        isPlaying={playerState.isPlaying}
        currentTime={playerState.currentTime}
        duration={podcast.duration_seconds || playerState.duration}
        volume={playerState.volume}
        playbackRate={playerState.playbackRate}
        error={playerState.error}
        chapters={chapters}
        onTogglePlay={togglePlay}
        onSeek={seekTo}
        onVolume={setVolume}
        onRate={setRate}
      />}

      {lowTranscriptCoverage && podcast.status === 'completed' && !episodeFailed && (
        <div role="status" className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between" style={{ background: 'rgba(245,158,11,0.08)', borderColor: 'rgba(245,158,11,0.28)' }}>
          <div className="flex items-start gap-3"><AlertTriangle size={17} className="mt-0.5 shrink-0" style={{ color: '#F59E0B' }} /><div><p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>This transcript may be incomplete</p><p className="mt-1 text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>We found about {speechRate} spoken words per minute. Long pauses, music, background noise, or quiet speech can lower this estimate. Check the transcript against the original audio before relying on its insights.</p></div></div>
          <button onClick={() => { setTab('transcript'); setSearchParams({ tab: 'transcript' }, { replace: true }); }} className="shrink-0 rounded-lg px-3 py-2 text-xs font-semibold" style={{ background: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border)' }}>Review transcript</button>
        </div>
      )}

      {/* Tab navigation */}
      <div className="flex gap-1 overflow-x-auto rounded-xl p-1" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => { setTab(key); setSearchParams(key === 'overview' ? {} : { tab: key }, { replace: true }); }}
              className="flex min-w-[7.5rem] flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-all"
              style={{
                background: tab === key ? 'rgba(139,92,246,0.15)' : 'transparent',
                border: tab === key ? '1px solid rgba(139,92,246,0.3)' : '1px solid transparent',
                color: tab === key ? 'var(--text-primary)' : 'var(--text-muted)',
              }}
            >
              <Icon size={14} style={{ color: tab === key ? 'var(--accent-purple)' : 'inherit' }} />
              {label}
            </button>
          ))}
      </div>

      {/* Tab content */}
      {tab === 'overview' && (
        <div className="space-y-6">
          <section className="rounded-2xl p-6 sm:p-8" style={{ background: 'linear-gradient(135deg, rgba(139,92,246,0.14), rgba(34,211,238,0.06))', border: '1px solid var(--border)' }}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--accent-violet)' }}><Sparkles size={16} /> Your episode brief</div>
                <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>The main ideas, ready to scan.</p>
              </div>
              <span className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs" style={{ background: 'var(--bg-card)', color: 'var(--text-secondary)' }}><Clock size={13} /> {podcast.duration_seconds ? fmtDur(podcast.duration_seconds) : 'Duration unavailable'} · {chapters.length} chapters</span>
            </div>
            {episodeBrief.length ? <ul className="mt-6 space-y-4">{episodeBrief.map((summary, index) => <li key={`${index}-${summary}`} className="flex gap-3 text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}><span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold" style={{ background: 'rgba(139,92,246,0.18)', color: 'var(--accent-violet)' }}>{index + 1}</span><span>{summary}</span></li>)}</ul> : <div className="mt-6 flex items-center gap-3 text-sm" style={{ color: 'var(--text-secondary)' }}><CircleHelp size={18} /> No brief is available yet. Open the chapters or transcript to explore this episode.</div>}
            <button onClick={() => { setTab('chapters'); setSearchParams({ tab: 'chapters' }, { replace: true }); }} className="mt-6 inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90" style={{ background: 'var(--gradient-primary)' }}><Headphones size={15} /> Explore chapters</button>
          </section>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { icon: Clock, label: 'Listening time', value: podcast.duration_seconds ? fmtDur(podcast.duration_seconds) : '—' },
              { icon: BookOpen, label: 'Chapters', value: chapters.length },
              { icon: FileText, label: 'Transcript', value: segmentsLoaded ? segments.length.toLocaleString() : 'Searchable' },
              { icon: Mic2, label: 'Words captured', value: podcast.word_count?.toLocaleString() || '—' },
            ].map(({ icon: Icon, label, value }) => <div key={label} className="rounded-xl p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}><div className="mb-2 flex items-center gap-2"><Icon size={14} style={{ color: 'var(--accent-cyan)' }} /><span className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</span></div><p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{value}</p></div>)}
          </div>

        </div>
      )}

      {tab === 'chapters' && (
        <div className="space-y-4">
          {chapters.length === 0 ? (
            <div className="text-center py-12" style={{ color: 'var(--text-muted)' }}>
              No chapters generated yet.
            </div>
          ) : (
            chapters.map(ch => (
              <ChapterCard
                key={ch.id}
                chapter={ch}
                isActive={
                  playerState.currentTime >= ch.start_time &&
                  playerState.currentTime < ch.end_time
                }
                onPlay={seekTo}
                onUpdated={(updated) => {
                  setChapters(prev => prev.map(c => c.id === updated.id ? updated : c));
                }}
              />
            ))
          )}
        </div>
      )}

      {tab === 'transcript' && (
        segmentsLoaded ? <TranscriptExplorer segments={segments} currentTime={playerState.currentTime} onSeek={seekTo} /> : transcriptError ? (
          <div className="rounded-2xl p-6 text-center" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{transcriptError}</p>
            <button onClick={() => setTranscriptRetry(value => value + 1)} className="mt-3 rounded-lg px-3 py-2 text-sm font-semibold" style={{ background: 'rgba(139,92,246,0.14)', color: 'var(--accent-violet)' }}>Try again</button>
          </div>
        ) : <div className="rounded-2xl p-6 text-center text-sm" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}><Loader2 size={18} className="mx-auto mb-2 animate-spin" />Loading transcript when you need it…</div>
      )}

      {tab === 'export' && (
        <ExportPanel podcast={podcast} />
      )}
    </div>
  );
}
