import React, { useState } from 'react';
import {
  Play, Copy, Check, Clock, Pencil, X, Save
} from 'lucide-react';
import type { Chapter } from '../../types';
import { updateChapter } from '../../services/api';
import toast from 'react-hot-toast';

function fmt(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
  return `${m}:${s.toString().padStart(2,'0')}`;
}

interface Props {
  chapter: Chapter;
  isActive: boolean;
  onPlay: (startTime: number) => void;
  onUpdated: (ch: Chapter) => void;
}

export function ChapterCard({ chapter, isActive, onPlay, onUpdated }: Props) {
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(chapter.title);
  const [editSummary, setEditSummary] = useState(chapter.summary || '');
  const [saving, setSaving] = useState(false);

  const duration = chapter.end_time - chapter.start_time;
  const titleWords = chapter.title.toLowerCase().split(/\s+/);
  const unhelpfulTitle = !chapter.title.trim() || titleWords.length < 2 || titleWords.every(word => ['the', 'and', 'but', 'its', 'it\'s', 'yeah', 'okay', 'really', '&'].includes(word.replace(/[.,]/g, '')));
  const displayTitle = unhelpfulTitle ? `Chapter ${chapter.chapter_number}` : chapter.title;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(chapter.summary || `${displayTitle} · ${fmt(chapter.start_time)}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Could not copy to clipboard');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateChapter(chapter.podcast_id, chapter.id, {
        title: editTitle,
        summary: editSummary,
      });
      onUpdated(updated);
      setEditing(false);
      toast.success('Chapter updated');
    } catch {
      toast.error('Failed to update chapter');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="rounded-2xl transition-all duration-300"
      style={{
        background: isActive ? 'var(--bg-card-hover)' : 'var(--bg-card)',
        border: isActive
          ? '1px solid rgba(139,92,246,0.4)'
          : '1px solid var(--border)',
        boxShadow: isActive ? '0 0 20px rgba(139,92,246,0.15)' : 'none',
      }}
    >
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start gap-4">
          {/* Chapter number bubble */}
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-bold text-white"
            style={{ background: 'var(--gradient-primary)' }}>
            {chapter.chapter_number}
          </div>

          <div className="flex-1 min-w-0">
            {editing ? (
              <input
                className="w-full bg-transparent border-b outline-none text-base font-semibold pb-1"
                style={{ color: 'var(--text-primary)', borderColor: 'var(--accent-purple)' }}
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
                autoFocus
              />
            ) : (
              <h3 className="font-semibold text-base leading-tight" style={{ color: 'var(--text-primary)' }}>
                {displayTitle}
              </h3>
            )}

            {/* Meta row */}
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                <Clock size={11} />
                {fmt(chapter.start_time)} → {fmt(chapter.end_time)}
              </span>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {Math.round(duration / 60)}m {Math.round(duration % 60)}s
              </span>
              {chapter.is_edited && (
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>• edited</span>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {editing ? (
              <>
                <button onClick={() => setEditing(false)}
                  className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                  style={{ color: 'var(--text-muted)' }}>
                  <X size={14} />
                </button>
                <button onClick={handleSave} disabled={saving}
                  className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                  style={{ color: '#34D399' }}>
                  {saving ? '…' : <Save size={14} />}
                </button>
              </>
            ) : (
              <>
                <button onClick={() => setEditing(true)}
                  className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                  style={{ color: 'var(--text-muted)' }}>
                  <Pencil size={13} />
                </button>
                <button onClick={handleCopy}
                  className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                  style={{ color: copied ? '#34D399' : 'var(--text-muted)' }}>
                  {copied ? <Check size={13} /> : <Copy size={13} />}
                </button>
              </>
            )}

            <button
              onClick={() => onPlay(chapter.start_time)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white transition-all hover:opacity-90"
              style={{ background: 'var(--gradient-primary)' }}
            >
              <Play size={11} />
              Play
            </button>

          </div>
        </div>

        {/* Summary */}
        <div className="mt-4 ml-13">
          {editing ? (
            <textarea
              className="w-full bg-transparent border rounded-xl outline-none text-sm p-3 resize-none"
              style={{
                color: 'var(--text-secondary)',
                borderColor: 'rgba(139,92,246,0.3)',
                minHeight: 100,
              }}
              value={editSummary}
              onChange={e => setEditSummary(e.target.value)}
              rows={4}
            />
          ) : (
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {chapter.summary || 'No summary available.'}
            </p>
          )}
        </div>
      </div>

    </div>
  );
}
