import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Mic2, Upload, Clock, BookOpen, ArrowUpRight, Loader2, Search, RefreshCw, FileText, Download } from 'lucide-react';
import { listPodcasts } from '../services/api';
import type { PodcastListItem } from '../types';

const statusStyle: Record<string, { bg: string; color: string; label: string }> = {
  completed: { bg: '#e9f5ed', color: '#34775c', label: 'Ready' },
  processing: { bg: '#fff5df', color: '#9a6a12', label: 'Processing' },
  pending: { bg: '#f1f3f2', color: '#697773', label: 'Queued' },
  failed: { bg: '#fff0ed', color: '#b55342', label: 'Needs attention' },
};
const viewCopy: Record<string, { title: string; description: string; icon: typeof Mic2 }> = {
  all: { title: 'Podcast library', description: 'Every episode you have added to your workspace.', icon: Mic2 },
  transcripts: { title: 'Transcripts', description: 'Open an episode to search and follow its transcript.', icon: FileText },
  chapters: { title: 'AI chapters', description: 'Browse generated chapters and jump to any moment.', icon: BookOpen },
  exports: { title: 'Export history', description: 'Choose an episode to download transcripts, chapters, or tagged audio.', icon: Download },
};
function formatDate(value: string) { return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
function formatDuration(value: number) { const hours = Math.floor(value / 3600); const minutes = Math.floor((value % 3600) / 60); return hours ? `${hours}h ${minutes}m` : `${minutes} min`; }

export function PodcastsPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const view = params.get('view') || 'all';
  const query = params.get('q')?.trim().toLowerCase() || '';
  const [podcasts, setPodcasts] = useState<PodcastListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const load = () => { setLoading(true); setError(''); listPodcasts().then(items => { setPodcasts(items); setHasMore(items.length === 50); }).catch(e => setError(e instanceof Error ? e.message : 'Could not load your library.')).finally(() => setLoading(false)); };
  const loadMore = () => { if (loadingMore || !hasMore) return; setLoadingMore(true); listPodcasts(50, podcasts.length).then(items => { setPodcasts(current => [...current, ...items]); setHasMore(items.length === 50); }).catch(e => setError(e instanceof Error ? e.message : 'Could not load more episodes.')).finally(() => setLoadingMore(false)); };
  useEffect(() => {
    let active = true;
    listPodcasts().then(items => {
      if (!active) return;
      setPodcasts(items);
      setHasMore(items.length === 50);
    }).catch(e => {
      if (active) setError(e instanceof Error ? e.message : 'Could not load your library.');
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);
  const filtered = useMemo(() => podcasts.filter(p => {
    const matchesSearch = !query || `${p.title} ${p.original_filename}`.toLowerCase().includes(query);
    const matchesStatus = filter === 'all' || p.status === filter;
    const matchesView = view === 'all' || p.status === 'completed';
    return matchesSearch && matchesStatus && matchesView;
  }), [podcasts, query, filter, view]);
  const content = viewCopy[view] || viewCopy.all;
  const Icon = content.icon;

  return <div className="animate-slide-up space-y-7">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[.15em]" style={{ color: 'var(--accent-purple)' }}><Icon size={14} /> Your workspace</div><h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>{content.title}</h1><p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>{content.description}</p></div>
      <button onClick={() => navigate('/upload')} className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white" style={{ background: 'var(--gradient-primary)' }}><Upload size={15} /> Add episode</button>
    </div>

    <div className="surface-card flex flex-wrap items-center justify-between gap-4 rounded-2xl p-4">
      <div className="flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ background: '#edf5ef', color: 'var(--accent-purple)' }}><Mic2 size={18} /></div><div><p className="text-lg font-semibold">{filtered.length}<span className="ml-1 text-sm font-normal" style={{ color: 'var(--text-muted)' }}>episode{filtered.length === 1 ? '' : 's'}</span></p><p className="text-xs" style={{ color: 'var(--text-muted)' }}>{query ? `Matching “${params.get('q')}” in loaded episodes` : hasMore ? 'Showing the latest episodes' : 'In your library'}</p></div></div>
      <div className="flex flex-wrap gap-1 rounded-xl p-1" style={{ background: '#f4f7f4' }}>
        {[['all', 'All'], ['completed', 'Ready'], ['processing', 'Processing'], ['failed', 'Needs attention']].map(([key, label]) => <button key={key} onClick={() => setFilter(key)} className="rounded-lg px-3 py-2 text-xs font-medium" style={{ color: filter === key ? 'var(--text-primary)' : 'var(--text-muted)', background: filter === key ? '#fff' : 'transparent', boxShadow: filter === key ? '0 1px 3px #17232212' : 'none' }}>{label}</button>)}
      </div>
    </div>

    {error ? <div className="surface-card rounded-2xl p-8 text-center"><p className="font-semibold">We couldn’t load the library</p><p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>{error}</p><button onClick={load} className="mt-4 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium" style={{ background: '#edf5ef', color: 'var(--accent-violet)' }}><RefreshCw size={14} /> Try again</button></div> : loading ? <div className="flex h-48 items-center justify-center"><Loader2 size={28} className="animate-spin" style={{ color: 'var(--accent-purple)' }} /></div> : filtered.length === 0 ? <div className="surface-card flex flex-col items-center rounded-2xl px-5 py-16 text-center"><div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: '#edf5ef', color: 'var(--accent-purple)' }}>{query ? <Search size={24} /> : <Mic2 size={24} />}</div><h2 className="text-lg font-semibold">{query ? 'No matching episodes' : filter !== 'all' ? 'Nothing in this filter yet' : view !== 'all' ? 'No completed episodes yet' : 'Your library starts here'}</h2><p className="mt-2 max-w-sm text-sm" style={{ color: 'var(--text-secondary)' }}>{query ? 'Try another title or filename.' : view !== 'all' ? 'Completed episodes will appear here after processing.' : 'Add a podcast and Podly will build a searchable transcript and chapter guide.'}</p>{!query && filter === 'all' && view === 'all' && <button onClick={() => navigate('/upload')} className="mt-5 flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white" style={{ background: 'var(--gradient-primary)' }}><Upload size={14} /> Add your first episode</button>}</div> : <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">{filtered.map(podcast => {
      const status = statusStyle[podcast.status] || statusStyle.pending;
      const targetTab = view === 'transcripts' ? 'transcript' : view === 'chapters' ? 'chapters' : view === 'exports' ? 'export' : 'overview';
      return <button key={podcast.id} onClick={() => navigate(`/podcasts/${podcast.id}?tab=${targetTab}`)} className="surface-card group rounded-2xl p-5 text-left transition hover:-translate-y-0.5 hover:shadow-md">
        <div className="flex items-start gap-4"><div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl" style={{ background: '#edf5ef', color: 'var(--accent-purple)' }}><Mic2 size={20} /></div><div className="min-w-0 flex-1"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><h2 className="truncate text-[15px] font-semibold" style={{ color: 'var(--text-primary)' }}>{podcast.title}</h2><p className="mt-1 truncate text-xs" style={{ color: 'var(--text-muted)' }}>{podcast.original_filename}</p></div><span className="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold" style={{ background: status.bg, color: status.color }}>{status.label}</span></div><div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs" style={{ color: 'var(--text-secondary)' }}>{podcast.duration_seconds != null && <span className="flex items-center gap-1.5"><Clock size={13} />{formatDuration(podcast.duration_seconds)}</span>}{podcast.word_count != null && <span>{podcast.word_count.toLocaleString()} words</span>}{podcast.topic_count != null && <span className="flex items-center gap-1.5"><BookOpen size={13} />{podcast.topic_count} topics</span>}<span className="ml-auto">{formatDate(podcast.created_at)}</span></div>{podcast.status === 'failed' && <p className="mt-3 rounded-lg px-3 py-2 text-xs" style={{ background: '#fff5f2', color: '#9b5144' }}>Processing stopped. Open for details or upload a valid audio file to try again.</p>}</div><ArrowUpRight size={16} className="mt-1 shrink-0 opacity-0 transition group-hover:opacity-100" style={{ color: 'var(--accent-purple)' }} /></div>
      </button>;
    })}</div>}
    {!loading && !error && hasMore && <div className="flex flex-col items-center gap-2"><button onClick={loadMore} disabled={loadingMore} className="rounded-xl px-4 py-2.5 text-sm font-semibold disabled:opacity-60" style={{ background: '#edf5ef', color: 'var(--accent-violet)' }}>{loadingMore ? 'Loading…' : 'Load more episodes'}</button>{query && <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Search covers loaded episodes. Load more to search older uploads.</p>}</div>}
  </div>;
}


