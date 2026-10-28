import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Mic2, FileText, BookOpen, Download, Settings, Sparkles, ChevronRight } from 'lucide-react';

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Overview' },
  { to: '/podcasts', icon: Mic2, label: 'Podcast library' },
  { to: '/podcasts?view=transcripts', icon: FileText, label: 'Transcripts' },
  { to: '/podcasts?view=chapters', icon: BookOpen, label: 'AI chapters' },
  { to: '/podcasts?view=exports', icon: Download, label: 'Export history' },
];

export function Sidebar() {
  const location = useLocation();
  return <aside className="sidebar hidden lg:flex min-h-screen flex-shrink-0 flex-col px-5 py-7">
    <NavLink to="/" className="mb-10 flex items-center gap-3 px-2 no-underline">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl text-white" style={{ background: 'var(--gradient-primary)' }}><Sparkles size={19} /></div>
      <div><div className="text-base font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>podly<span style={{ color: 'var(--accent-purple)' }}>.</span></div><div className="text-[10px] font-semibold uppercase tracking-[.16em]" style={{ color: 'var(--text-muted)' }}>Podcast studio</div></div>
    </NavLink>
    <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.15em]" style={{ color: 'var(--text-muted)' }}>Workspace</p>
    <nav className="flex flex-1 flex-col gap-1" aria-label="Main navigation">
      {nav.map(({ to, icon: Icon, label }) => {
        const [path, search = ''] = to.split('?');
        const active = location.pathname === path && (location.search.replace(/^\?/, '') === search);
        return <NavLink key={to} to={to} end={path === '/'} className="sidebar-link flex items-center gap-3 rounded-xl border px-3 py-3 text-[13px] font-medium no-underline transition-colors" style={{ color: active ? 'var(--accent-violet)' : 'var(--text-secondary)', background: active ? '#edf5ef' : 'transparent', borderColor: active ? '#dcebe0' : 'transparent' }}><Icon size={17} />{label}{active && <ChevronRight size={14} className="ml-auto" />}</NavLink>;
      })}
    </nav>
    <NavLink to="/settings" className="sidebar-link flex items-center gap-3 rounded-xl border px-3 py-3 text-[13px] font-medium no-underline" style={{ color: location.pathname === '/settings' ? 'var(--accent-violet)' : 'var(--text-secondary)', borderColor: 'transparent' }}><Settings size={17} />Settings</NavLink>
    <div className="mt-6 rounded-2xl p-4" style={{ background: 'var(--gradient-card)', border: '1px solid var(--border)' }}><div className="mb-2 flex items-center gap-2 text-xs font-semibold" style={{ color: 'var(--accent-violet)' }}><Sparkles size={13} />Made for deep listening</div><p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-muted)' }}>Turn long-form audio into a searchable, chaptered library.</p></div>
    <div className="mt-5 border-t pt-4 text-[11px]" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>Podly AI <span className="float-right">v1.0</span></div>
  </aside>;
}
