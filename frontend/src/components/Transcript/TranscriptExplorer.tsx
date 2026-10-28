import React, { useState, useMemo } from 'react';
import { Search, Clock, FileText } from 'lucide-react';
import type { TranscriptSegment } from '../../types';

function fmt(sec: number) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

interface Props {
  segments: TranscriptSegment[];
  currentTime?: number;
  onSeek?: (t: number) => void;
}

export function TranscriptExplorer({ segments, currentTime = 0, onSeek }: Props) {
  const [query, setQuery] = useState('');
  const [visibleCount, setVisibleCount] = useState(100);

  const filtered = useMemo(() => {
    if (!query.trim()) return segments;
    const q = query.toLowerCase();
    return segments.filter(s => s.text.toLowerCase().includes(q));
  }, [segments, query]);

  const isActive = (seg: TranscriptSegment) =>
    currentTime >= seg.start_time && currentTime < seg.end_time;

  const highlightText = (text: string) => {
    if (!query.trim()) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      i % 2 === 1
        ? <mark key={i} style={{ background: 'rgba(139,92,246,0.3)', color: 'var(--text-primary)', borderRadius: 3 }}>{part}</mark>
        : part
    );
  };

  return (
    <div className="rounded-2xl overflow-hidden"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>

      {/* Search header */}
      <div className="p-4" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)' }}>
          <Search size={14} style={{ color: 'var(--text-muted)' }} />
          <input
            className="bg-transparent outline-none text-sm flex-1"
            style={{ color: 'var(--text-primary)' }}
            placeholder="Search transcript…"
            value={query}
            onChange={e => { setQuery(e.target.value); setVisibleCount(100); }}
          />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {query ? `${filtered.length} match${filtered.length !== 1 ? 'es' : ''}` : `${Math.min(visibleCount, filtered.length)} of ${filtered.length} lines`}
          </span>
        </div>
      </div>

      {/* Segments */}
      <div className="overflow-y-auto" style={{ maxHeight: 520 }}>
        {segments.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-12"><FileText size={28} style={{ color: 'var(--text-muted)', opacity: 0.45 }} /><p className="text-sm" style={{ color: 'var(--text-muted)' }}>No transcript text was found for this episode.</p></div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <Search size={32} style={{ color: 'var(--text-muted)', opacity: 0.4 }} />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No results for "{query}"</p>
          </div>
        ) : (
          filtered.slice(0, visibleCount).map(seg => (
            <div
              key={seg.id}
              className="flex gap-3 px-4 py-3 transition-all hover:bg-white/3"
              style={{
                background: isActive(seg) ? 'rgba(139,92,246,0.08)' : 'transparent',
                borderLeft: isActive(seg) ? '3px solid var(--accent-purple)' : '3px solid transparent',
              }}
            >
              {/* Timestamp */}
              <button
                className="flex items-center gap-1 text-xs font-mono flex-shrink-0 pt-0.5 hover:underline"
                aria-label={`Play from ${fmt(seg.start_time)}`}
                style={{ color: isActive(seg) ? 'var(--accent-cyan)' : 'var(--text-muted)', minWidth: 50 }}
                onClick={e => { e.stopPropagation(); onSeek?.(seg.start_time); }}
              >
                <Clock size={10} />
                {fmt(seg.start_time)}
              </button>

              {/* Text */}
              <p className="text-sm leading-relaxed flex-1"
                style={{ color: isActive(seg) ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                {highlightText(seg.text)}
              </p>

              {/* Topic pill */}
              {seg.topic_label && seg.topic_label !== 'Miscellaneous' && (
                <span className="text-xs px-2 py-0.5 rounded-full flex-shrink-0 self-start"
                  style={{
                    background: 'rgba(34,211,238,0.08)',
                    border: '1px solid rgba(34,211,238,0.15)',
                    color: 'var(--accent-cyan)',
                  }}>
                  {seg.topic_label.split(',')[0].trim()}
                </span>
              )}
            </div>
          ))
        )}
        {filtered.length > visibleCount && <div className="flex justify-center border-t p-3" style={{ borderColor: 'var(--border)' }}><button onClick={() => setVisibleCount(count => count + 100)} className="rounded-lg px-4 py-2 text-sm font-medium" style={{ color: 'var(--accent-violet)', background: 'rgba(139,92,246,0.1)' }}>Load next {Math.min(100, filtered.length - visibleCount)} lines</button></div>}
      </div>
    </div>
  );
}
