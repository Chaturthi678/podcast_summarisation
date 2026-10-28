import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface Props {
  icon: LucideIcon;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
  loading?: boolean;
}

export function StatCard({ icon: Icon, label, value, sub, color = 'var(--accent-purple)', loading }: Props) {
  return (
    <div
      className="metric-card surface-card flex items-start gap-4 rounded-2xl transition-all hover:-translate-y-0.5 hover:shadow-sm"
      style={{ transitionDuration: '200ms' }}
    >
      <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
        style={{ background: '#f0f5f1', border: '1px solid #e2ece5' }}>
        <Icon size={20} style={{ color }} />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-xs uppercase tracking-wider mb-1 font-medium" style={{ color: 'var(--text-muted)' }}>
          {label}
        </p>
        {loading ? (
          <div className="skeleton h-7 w-24 rounded" />
        ) : (
          <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            {value}
          </p>
        )}
        {sub && !loading && (
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
            {sub}
          </p>
        )}
      </div>
    </div>
  );
}
