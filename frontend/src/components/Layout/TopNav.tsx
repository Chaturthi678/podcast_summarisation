import React, { useState } from 'react';
import { Search, Upload, Sparkles } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

export function TopNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const [draft, setDraft] = useState<{ search: string; value: string } | null>(null);
  const query = draft?.search === location.search
    ? draft.value
    : new URLSearchParams(location.search).get('q') || '';
  const search = (event: React.FormEvent) => {
    event.preventDefault();
    const value = query.trim();
    navigate(value ? `/podcasts?q=${encodeURIComponent(value)}` : '/podcasts');
  };
  return <header className="topnav sticky top-0 z-40 flex flex-shrink-0 items-center gap-5 backdrop-blur-xl">
    <div className="hidden items-center gap-2 lg:flex"><div className="flex h-9 w-9 items-center justify-center rounded-xl text-white" style={{ background: 'var(--gradient-primary)' }}><Sparkles size={16} /></div><span className="font-bold tracking-tight">podly<span style={{ color: 'var(--accent-purple)' }}>.</span></span></div>
    <form onSubmit={search} className="topnav-search flex w-full max-w-md items-center gap-2 rounded-xl px-3 py-2.5">
      <Search size={16} style={{ color: 'var(--text-muted)' }} />
      <input aria-label="Search podcasts" className="min-w-0 flex-1 bg-transparent text-sm outline-none" style={{ color: 'var(--text-primary)' }} placeholder="Search your library…" value={query} onChange={e => setDraft({ search: location.search, value: e.target.value })} />
      <span className="hidden rounded border px-1.5 py-0.5 text-[10px] sm:inline" style={{ color: 'var(--text-muted)', borderColor: 'var(--border)' }}>ENTER</span>
    </form>
    <button aria-label="Upload a new episode" onClick={() => navigate('/upload')} className="ml-auto flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-105" style={{ background: 'var(--gradient-primary)', boxShadow: '0 5px 14px rgba(57,134,110,.18)' }}><Upload size={15} /><span className="topnav-upload-label">New episode</span></button>
  </header>;
}
