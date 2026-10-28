import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic2, BookOpen, FileText, Clock, Sparkles, ArrowRight, Upload } from 'lucide-react';
import { StatCard } from '../components/Dashboard/StatCard';
import { getApiError, getDashboardStats, listPodcasts } from '../services/api';
import type { DashboardStats, PodcastListItem } from '../types';

function fmtDuration(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

const statusStyle: Record<string, { bg: string; color: string; label: string }> = {
  completed:  { bg: 'rgba(52,211,153,0.1)',  color: '#34D399', label: 'Completed'  },
  processing: { bg: 'rgba(251,191,36,0.1)',  color: '#FCD34D', label: 'Processing' },
  pending:    { bg: 'rgba(251,191,36,0.1)',  color: '#FCD34D', label: 'Pending'    },
  failed:     { bg: 'rgba(239,68,68,0.1)',   color: '#F87171', label: 'Failed'     },
};

export function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recent, setRecent] = useState<PodcastListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([getDashboardStats(), listPodcasts()])
      .then(([s, p]) => { setStats(s); setRecent(p.slice(0, 5)); })
      .catch(err => setError(getApiError(err, 'Could not load your dashboard.')))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Welcome */}
      <div className="dashboard-hero surface-card relative overflow-hidden rounded-3xl">
        {/* Glow orbs */}
        <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full opacity-20 pointer-events-none"
          style={{ background: 'radial-gradient(circle, var(--accent-purple) 0%, transparent 70%)' }} />
        <div className="absolute -bottom-10 -left-10 w-48 h-48 rounded-full opacity-10 pointer-events-none"
          style={{ background: 'radial-gradient(circle, var(--accent-cyan) 0%, transparent 70%)' }} />

        <div className="relative">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={16} style={{ color: 'var(--accent-purple)' }} />
            <span className="text-sm font-medium" style={{ color: 'var(--accent-violet)' }}>
              AI-Powered Podcast Intelligence
            </span>
          </div>
            <h1 className="mb-3 font-bold" style={{ color: 'var(--text-primary)' }}>
            Your listening, <span className="gradient-text">made useful.</span>
          </h1>
          <p className="mb-7 max-w-xl text-base" style={{ color: 'var(--text-secondary)' }}>
            Search every conversation, jump straight to the good parts, and take your notes anywhere.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => navigate('/upload')}
              className="flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold text-white transition hover:brightness-105"
              style={{ background: 'var(--gradient-primary)', boxShadow: '0 7px 18px rgba(57,134,110,0.2)' }}
            >
              <Upload size={16} />
              Analyze New Podcast
              <ArrowRight size={14} />
            </button>
            <button
              onClick={() => navigate('/podcasts')}
              className="flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-medium transition-all hover:bg-white/50"
              style={{ border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
            >
              View My Podcasts
            </button>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Mic2}
          label="Podcasts Analyzed"
          value={stats?.completed_podcasts ?? 0}
          sub={`${stats?.total_podcasts ?? 0} total uploads`}
          color="var(--accent-purple)"
          loading={loading}
        />
        <StatCard
          icon={Clock}
          label="Audio Duration"
          value={stats ? fmtDuration(stats.total_duration_seconds) : '0m'}
          sub="Total processed"
          color="var(--accent-cyan)"
          loading={loading}
        />
        <StatCard
          icon={BookOpen}
          label="Chapters Generated"
          value={stats?.total_chapters ?? 0}
          sub="AI-created chapters"
          color="#F59E0B"
          loading={loading}
        />
        <StatCard
          icon={FileText}
          label="Words Transcribed"
          value={stats ? `${(stats.total_words / 1000).toFixed(1)}K` : '0'}
          sub="Via Whisper ASR"
          color="#EC4899"
          loading={loading}
        />
      </div>

      {/* Recent podcasts */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            Recent Podcasts
          </h2>
          <button onClick={() => navigate('/podcasts')}
            className="flex items-center gap-1 text-sm transition-colors hover:opacity-80"
            style={{ color: 'var(--accent-violet)' }}>
            View all <ArrowRight size={13} />
          </button>
        </div>

      {error && !loading ? (
        <div className="surface-card rounded-2xl p-6 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>Your dashboard couldn’t load</p>
          <p className="mt-1">{error}</p>
          <button onClick={() => { setLoading(true); setError(''); Promise.all([getDashboardStats(), listPodcasts()]).then(([s, p]) => { setStats(s); setRecent(p.slice(0, 5)); }).catch(err => setError(getApiError(err))).finally(() => setLoading(false)); }} className="mt-3 rounded-lg px-3 py-2 text-sm font-medium" style={{ background: '#edf5ef', color: 'var(--accent-violet)' }}>Try again</button>
        </div>
      ) : recent.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center py-16 rounded-2xl gap-4"
            style={{ border: '2px dashed rgba(139,92,246,0.2)', background: 'rgba(139,92,246,0.02)' }}>
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)' }}>
              <Mic2 size={28} style={{ color: 'var(--accent-purple)' }} />
            </div>
            <div className="text-center">
              <p className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>No podcasts yet</p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Upload your first podcast to get started</p>
            </div>
            <button onClick={() => navigate('/upload')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
              style={{ background: 'var(--gradient-primary)' }}>
              <Upload size={14} />
              Upload Now
            </button>
          </div>
        ) : (
          <div className="rounded-2xl overflow-hidden"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            {recent.map((pod, i) => {
              const s = statusStyle[pod.status] || statusStyle.pending;
              return (
                <div
                  key={pod.id}
                  onClick={() => navigate(`/podcasts/${pod.id}`)}
                  className="flex cursor-pointer items-center gap-4 p-4 text-left transition-colors hover:bg-[#f7faf7]"
                  style={{
                    borderBottom: i < recent.length - 1 ? '1px solid var(--border)' : 'none',
                  }}
                >
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)' }}>
                    <Mic2 size={17} style={{ color: 'var(--accent-purple)' }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate" style={{ color: 'var(--text-primary)' }}>
                      {pod.title}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                      {fmtDate(pod.created_at)}
                      {pod.duration_seconds ? ` · ${fmtDuration(pod.duration_seconds)}` : ''}
                      {pod.word_count ? ` · ${pod.word_count.toLocaleString()} words` : ''}
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-medium flex-shrink-0"
                    style={{ background: s.bg, color: s.color }}>
                    {s.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
