import React from 'react';
import {
  Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Gauge
} from 'lucide-react';
import type { Chapter } from '../../types';

function fmt(sec: number) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

interface Props {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  error?: string | null;
  chapters: Chapter[];
  onTogglePlay: () => void;
  onSeek: (t: number) => void;
  onVolume: (v: number) => void;
  onRate: (r: number) => void;
}

const RATES = [0.75, 1, 1.25, 1.5, 1.75, 2];

export function AudioPlayer({
  isPlaying, currentTime, duration, volume, playbackRate,
  chapters, error, onTogglePlay, onSeek, onVolume, onRate,
}: Props) {
  const pct = duration > 0 ? (currentTime / duration) * 100 : 0;

  // Find active chapter
  const activeChapter = chapters.find(
    ch => currentTime >= ch.start_time && currentTime < ch.end_time
  );

  const handleSeekClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    onSeek(ratio * duration);
  };

  const nextRate = () => {
    const idx = RATES.indexOf(playbackRate);
    onRate(RATES[(idx + 1) % RATES.length]);
  };

  return (
    <div className="surface-card space-y-4 rounded-2xl p-5"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>

      {error && <p role="alert" className="rounded-lg px-3 py-2 text-xs" style={{ background: '#fff1ed', color: '#a74f40' }}>{error}</p>}

      {/* Active chapter label */}
      {activeChapter && (
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full animate-pulse"
            style={{ background: 'var(--accent-purple)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--accent-violet)' }}>
            Ch. {activeChapter.chapter_number}: {activeChapter.title}
          </span>
        </div>
      )}

      {/* Seek bar with chapter markers */}
      <div className="space-y-1">
        <div
          className="h-2 rounded-full cursor-pointer relative overflow-visible group"
          style={{ background: 'rgba(255,255,255,0.07)' }}
          onClick={handleSeekClick}
        >
          {/* Progress fill */}
          <div className="h-full rounded-full transition-all"
            style={{
              width: `${pct}%`,
              background: 'var(--gradient-primary)',
            }} />

          {/* Chapter markers */}
          {chapters.map(ch => (
            <button
              key={ch.id}
              title={ch.title}
              onClick={e => { e.stopPropagation(); onSeek(ch.start_time); }}
              className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full transition-transform hover:scale-150"
              style={{
                left: `${(ch.start_time / duration) * 100}%`,
                background: 'var(--accent-cyan)',
                border: '1.5px solid var(--bg-card)',
                transform: 'translate(-50%, -50%)',
              }}
            />
          ))}

          {/* Thumb */}
          <div className="absolute top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full shadow-lg"
            style={{
              left: `${pct}%`,
              transform: 'translate(-50%, -50%)',
              background: 'white',
              boxShadow: '0 0 8px rgba(139,92,246,0.6)',
            }} />
        </div>

        <div className="flex justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
          <span>{fmt(currentTime)}</span>
          <span>{fmt(duration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        {/* Skip back 10s */}
        <button onClick={() => onSeek(Math.max(0, currentTime - 10))}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          style={{ color: 'var(--text-secondary)' }}>
          <SkipBack size={18} />
        </button>

        {/* Play/Pause */}
        <button
          onClick={onTogglePlay}
          className="w-11 h-11 rounded-xl flex items-center justify-center transition-all hover:scale-105"
          style={{
            background: 'var(--gradient-primary)',
            boxShadow: '0 0 20px rgba(139,92,246,0.4)',
          }}
        >
          {isPlaying
            ? <Pause size={18} className="text-white" />
            : <Play size={18} className="text-white ml-0.5" />
          }
        </button>

        {/* Skip forward 10s */}
        <button onClick={() => onSeek(Math.min(duration, currentTime + 10))}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          style={{ color: 'var(--text-secondary)' }}>
          <SkipForward size={18} />
        </button>

        {/* Playback rate */}
        <button onClick={nextRate}
          className="ml-2 flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-mono transition-colors hover:bg-white/5"
          style={{ color: 'var(--accent-cyan)', border: '1px solid rgba(34,211,238,0.2)' }}>
          <Gauge size={12} />
          {playbackRate}×
        </button>

        {/* Volume */}
        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => onVolume(volume > 0 ? 0 : 1)}
            className="p-1 hover:bg-white/5 rounded transition-colors"
            style={{ color: 'var(--text-secondary)' }}>
            {volume === 0 ? <VolumeX size={15} /> : <Volume2 size={15} />}
          </button>
          <input
            type="range" min={0} max={1} step={0.05}
            value={volume}
            onChange={e => onVolume(parseFloat(e.target.value))}
            className="w-20 h-1 accent-purple-500 cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}
