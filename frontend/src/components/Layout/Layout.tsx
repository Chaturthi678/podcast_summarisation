import React from 'react';
import { Sidebar } from './Sidebar';
import { TopNav } from './TopNav';
import { Outlet } from 'react-router-dom';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Mic2, Settings } from 'lucide-react';

export function Layout() {
  return (
    <div className="app-layout flex min-h-screen" style={{ background: 'var(--bg-base)' }}>
      <Sidebar />
      <div className="app-main flex flex-col flex-1 min-w-0">
        <TopNav />
        <main className="page-content flex-1 overflow-auto">
          <Outlet />
        </main>
        <nav className="mobile-nav hidden fixed bottom-0 inset-x-0 z-50 justify-around border-t bg-white/95 px-3 py-2 backdrop-blur-lg" style={{ borderColor: 'var(--border)' }} aria-label="Mobile navigation">
          {[
            { to: '/', label: 'Home', icon: LayoutDashboard },
            { to: '/podcasts', label: 'Library', icon: Mic2 },
            { to: '/settings', label: 'Settings', icon: Settings },
          ].map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} className="flex min-w-16 flex-col items-center gap-1 rounded-lg px-3 py-1.5 text-[11px]" style={({ isActive }) => ({ color: isActive ? 'var(--accent-purple)' : 'var(--text-muted)' })}><Icon size={18} />{label}</NavLink>)}
        </nav>
      </div>
    </div>
  );
}
