import React, { useCallback, useState } from 'react';
import { Upload, Music, AlertCircle, CheckCircle2 } from 'lucide-react';

interface UploadZoneProps {
  onFile: (file: File) => void;
  disabled?: boolean;
}

const ALLOWED = ['.mp3', '.wav', '.m4a', '.ogg', '.flac'];
const MAX_MB = 500;

export function UploadZone({ onFile, disabled }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) return `Unsupported format. Use: ${ALLOWED.join(', ')}`;
    if (file.size > MAX_MB * 1024 * 1024) return `File too large (max ${MAX_MB} MB)`;
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const err = validate(file);
    if (err) { setError(err); return; }
    setError(null);
    onFile(file);
  }, [onFile]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div>
      <label
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className="relative flex flex-col items-center justify-center gap-5 rounded-2xl cursor-pointer transition-all duration-300"
        style={{
          minHeight: 280,
          border: dragging
            ? '2px solid var(--accent-purple)'
            : '2px dashed rgba(139,92,246,0.3)',
          background: dragging
            ? 'rgba(139,92,246,0.08)'
            : 'rgba(139,92,246,0.03)',
          boxShadow: dragging ? 'var(--glow-purple)' : 'none',
          opacity: disabled ? 0.5 : 1,
          pointerEvents: disabled ? 'none' : 'auto',
        }}
      >
        <input
          type="file"
          accept={ALLOWED.join(',')}
          className="hidden"
          onChange={onInput}
          disabled={disabled}
        />

        {/* Icon area */}
        <div className="w-20 h-20 rounded-2xl flex items-center justify-center transition-all"
          style={{
            background: dragging ? 'rgba(139,92,246,0.2)' : 'rgba(139,92,246,0.1)',
            border: '1px solid rgba(139,92,246,0.3)',
          }}>
          {dragging
            ? <CheckCircle2 size={36} style={{ color: 'var(--accent-purple)' }} />
            : <Upload size={36} style={{ color: 'var(--accent-purple)' }} />
          }
        </div>

        <div className="text-center px-6">
          <p className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
            {dragging ? 'Drop to upload' : 'Drag & drop your podcast'}
          </p>
          <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>
            or click to browse files
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {ALLOWED.map(ext => (
              <span key={ext} className="px-2 py-0.5 rounded-md text-xs font-mono"
                style={{
                  background: 'rgba(139,92,246,0.1)',
                  border: '1px solid rgba(139,92,246,0.2)',
                  color: 'var(--accent-violet)',
                }}>
                {ext.toUpperCase()}
              </span>
            ))}
          </div>
          <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
            Maximum file size: {MAX_MB} MB
          </p>
        </div>

        {/* Decorative corner icons */}
        <Music size={18} className="absolute top-4 right-4 opacity-20"
          style={{ color: 'var(--accent-cyan)' }} />
        <Music size={14} className="absolute bottom-6 left-6 opacity-10"
          style={{ color: 'var(--accent-purple)' }} />
      </label>

      {error && (
        <div className="mt-3 flex items-center gap-2 px-4 py-3 rounded-xl text-sm"
          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#FCA5A5' }}>
          <AlertCircle size={15} />
          {error}
        </div>
      )}
    </div>
  );
}
