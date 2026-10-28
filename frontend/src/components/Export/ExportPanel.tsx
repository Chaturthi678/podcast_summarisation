import React, { useState } from 'react';
import {
  Download, FileText, File, Music,
  CheckCircle2, Loader2, ChevronDown, Sparkles
} from 'lucide-react';
import type { Podcast } from '../../types';
import { downloadExport, getApiError } from '../../services/api';
import toast from 'react-hot-toast';

interface Props {
  podcast: Podcast;
}

const QUICK_FORMATS = [
  {
    key: 'md' as const,
    label: 'Episode brief',
    ext: '.MD',
    icon: Sparkles,
    desc: 'A clean, skimmable outline with chapter summaries',
    color: '#A78BFA',
  },
  {
    key: 'mp3' as const,
    label: 'Audio with chapters',
    ext: '.MP3',
    icon: Music,
    desc: 'Listen with chapter markers in a compatible player',
    color: '#F59E0B',
  },
];

const MORE_FORMATS = [
  {
    key: 'txt' as const,
    label: 'Full transcript',
    ext: '.TXT',
    icon: FileText,
    desc: 'Searchable text with timestamps',
    color: '#60A5FA',
  },
  {
    key: 'json' as const,
    label: 'Analysis data',
    ext: '.JSON',
    icon: File,
    desc: 'Complete analysis data as JSON',
    color: '#34D399',
  },
];

export function ExportPanel({ podcast }: Props) {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [done, setDone] = useState<Set<string>>(new Set());

  const handleDownload = async (format: 'txt' | 'md' | 'json' | 'mp3') => {
    setDownloading(format);
    try {
      const blob = await downloadExport(podcast.id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${podcast.title}.${format}`;
      a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setDone(prev => new Set([...prev, format]));
      toast.success(`${format.toUpperCase()} downloaded!`);
    } catch (error) {
      toast.error(getApiError(error, `Failed to download ${format.toUpperCase()}`));
    } finally {
      setTimeout(() => setDownloading(null), 800);
    }
  };

  return (
    <div className="rounded-2xl overflow-hidden"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>

      <div className="p-5" style={{ borderBottom: '1px solid var(--border)' }}>
        <h3 className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>Keep what matters</h3>
        <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>Save a quick episode brief or keep listening with chapter markers.</p>
      </div>

      <div className="grid grid-cols-1 gap-3 p-5 sm:grid-cols-2">
        {QUICK_FORMATS.map(({ key, label, ext, icon: Icon, desc, color }) => {
          const isLoading = downloading === key;
          const isDone = done.has(key);

          return (
            <button
              key={key}
              onClick={() => handleDownload(key)}
              disabled={isLoading}
              className="flex items-start gap-4 p-4 rounded-xl text-left transition-all hover:bg-white/5 hover:border-white/10 group"
              style={{ border: '1px solid var(--border)' }}
            >
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: `${color}18`, border: `1px solid ${color}30` }}>
                {isLoading
                  ? <Loader2 size={18} className="animate-spin" style={{ color }} />
                  : isDone
                  ? <CheckCircle2 size={18} style={{ color: '#34D399' }} />
                  : <Icon size={18} style={{ color }} />
                }
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                    {label}
                  </span>
                  <span className="text-xs font-mono px-1.5 py-0.5 rounded"
                    style={{ background: `${color}15`, color }}>
                    {ext}
                  </span>
                </div>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                  {desc}
                </p>
              </div>
              <Download size={14} className="flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ color: 'var(--text-muted)' }} />
            </button>
          );
        })}
      </div>

      <details className="group border-t" style={{ borderColor: 'var(--border)' }}>
        <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
          <span>More formats · transcript and data</span>
          <ChevronDown size={16} className="transition-transform group-open:rotate-180" />
        </summary>
        <div className="grid grid-cols-1 gap-3 px-5 pb-5 sm:grid-cols-2">
          {MORE_FORMATS.map(({ key, label, ext, icon: Icon, desc, color }) => {
            const isLoading = downloading === key;
            const isDone = done.has(key);
            return <button key={key} onClick={() => handleDownload(key)} disabled={isLoading} className="group/card flex items-start gap-4 rounded-xl p-4 text-left transition-all hover:bg-white/5 disabled:opacity-60" style={{ border: '1px solid var(--border)' }}>
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" style={{ background: `${color}18`, border: `1px solid ${color}30` }}>{isLoading ? <Loader2 size={18} className="animate-spin" style={{ color }} /> : isDone ? <CheckCircle2 size={18} style={{ color: '#34D399' }} /> : <Icon size={18} style={{ color }} />}</div>
              <div className="min-w-0 flex-1"><div className="flex items-center gap-2"><span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{label}</span><span className="rounded px-1.5 py-0.5 font-mono text-xs" style={{ background: `${color}15`, color }}>{ext}</span></div><p className="mt-0.5 text-xs" style={{ color: 'var(--text-muted)' }}>{desc}</p></div>
              <Download size={14} className="mt-0.5 shrink-0 opacity-0 transition-opacity group-hover/card:opacity-100" style={{ color: 'var(--text-muted)' }} />
            </button>;
          })}
        </div>
      </details>
    </div>
  );
}
