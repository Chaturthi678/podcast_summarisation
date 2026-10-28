import React from 'react';
import { Cpu, Database, Zap } from 'lucide-react';

export function SettingsPage() {
  return (
    <div className="space-y-6 animate-slide-up max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Settings</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          Configure AI models and processing options
        </p>
      </div>

      {[
        {
          icon: Cpu,
          title: 'Whisper ASR Model',
          desc: 'Fast CPU transcription with the smallest available Whisper model.',
          items: [
            { label: 'Preferred Model', value: 'tiny (uses cached base if needed)' },
            { label: 'Device', value: 'CPU' },
            { label: 'Decoding', value: 'Fast beam search · word alignment off' },
          ],
          color: 'var(--accent-purple)',
        },
        {
          icon: Zap,
          title: 'BERTopic & Summarizer',
          desc: 'Quick chapter generation avoids long embedding and summarization model downloads.',
          items: [
            { label: 'Fast topics', value: 'Transcript keyword groups' },
            { label: 'Chapter highlights', value: 'Fast extractive summaries' },
            { label: 'Deep analysis', value: 'Enable FAST_PROCESSING=false' },
          ],
          color: 'var(--accent-cyan)',
        },
        {
          icon: Database,
          title: 'Storage',
          desc: 'File storage configuration for uploads and processed outputs.',
          items: [
            { label: 'Upload Directory', value: 'backend/uploads/' },
            { label: 'Output Directory', value: 'backend/outputs/' },
            { label: 'Database', value: 'SQLite (podly.db)' },
          ],
          color: '#F59E0B',
        },
      ].map(({ icon: Icon, title, desc, items, color }) => (
        <div key={title} className="rounded-2xl p-5"
          style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: `${color}18`, border: `1px solid ${color}30` }}>
              <Icon size={17} style={{ color }} />
            </div>
            <div>
              <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{title}</h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{desc}</p>
            </div>
          </div>
          <div className="space-y-2">
            {items.map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between text-sm py-2"
                style={{ borderBottom: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
                <span className="font-mono text-xs px-2 py-0.5 rounded"
                  style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)' }}>
                  {value}
                </span>
              </div>
            ))}
          </div>
          <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
            Change these in <code className="font-mono" style={{ color: 'var(--accent-cyan)' }}>backend/.env</code> or <code className="font-mono" style={{ color: 'var(--accent-cyan)' }}>backend/app/config.py</code>
          </p>
        </div>
      ))}
    </div>
  );
}
