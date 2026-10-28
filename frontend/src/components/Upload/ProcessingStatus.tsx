import React from 'react';
import { CheckCircle2, Loader2, XCircle, Clock } from 'lucide-react';
import type { JobStatus } from '../../types';
import { PROCESSING_STAGES } from '../../types';
import { friendlyProcessingError } from '../../services/api';

interface Props {
  job: JobStatus;
  filename?: string;
  connectionError?: string | null;
}

export function ProcessingStatus({ job, filename, connectionError }: Props) {
  const currentStage = PROCESSING_STAGES.find(s => s.key === job.stage);
  const isFailed = job.stage === 'failed';
  const isComplete = job.stage === 'completed';

  const activeSteps = PROCESSING_STAGES.filter(s => s.step >= 0);

  return (
    <div className="rounded-2xl p-6 space-y-6"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>
            Processing Podcast
          </h3>
          {filename && (
            <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
              {filename}
            </p>
          )}
        </div>
        {isFailed
          ? <XCircle size={22} style={{ color: '#F87171' }} />
          : isComplete
          ? <CheckCircle2 size={22} style={{ color: '#34D399' }} />
          : <Loader2 size={22} className="animate-spin" style={{ color: 'var(--accent-purple)' }} />
        }
      </div>

      {/* Overall progress bar */}
      <div>
        <div className="flex justify-between text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
          <span>{job.message || currentStage?.label || job.stage}</span>
          <span>{Math.round(job.progress * 100)}%</span>
        </div>
        <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${job.progress * 100}%`,
              background: isFailed
                ? 'linear-gradient(90deg,#F87171,#EF4444)'
                : 'var(--gradient-primary)',
              boxShadow: isFailed ? 'none' : '0 0 10px rgba(139,92,246,0.5)',
            }}
          />
        </div>
      </div>

      {connectionError && <p role="status" className="rounded-lg px-3 py-2 text-xs" style={{ background: '#fff7e8', color: '#8b661e' }}>Reconnecting to the processing service. Your job is still running.</p>}

      {/* Stage checklist */}
      <div className="space-y-3">
        {activeSteps.map((stage) => {
          const isDone = currentStage && !isFailed && stage.step < currentStage.step;
          const isCurrent = stage.key === job.stage && !isFailed;
          return (
            <div key={stage.key} className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                style={{
                  background: isDone || isComplete
                    ? 'rgba(52,211,153,0.15)'
                    : isCurrent
                    ? 'rgba(139,92,246,0.15)'
                    : 'rgba(255,255,255,0.05)',
                  border: `1px solid ${isDone || isComplete ? 'rgba(52,211,153,0.4)' : isCurrent ? 'rgba(139,92,246,0.4)' : 'rgba(255,255,255,0.08)'}`,
                }}>
                {isDone || isComplete
                  ? <CheckCircle2 size={13} style={{ color: '#34D399' }} />
                  : isCurrent
                  ? <Loader2 size={13} className="animate-spin" style={{ color: 'var(--accent-purple)' }} />
                  : <Clock size={13} style={{ color: 'var(--text-muted)' }} />
                }
              </div>
              <span className="text-sm"
                style={{
                  color: isDone || isComplete ? '#34D399'
                    : isCurrent ? 'var(--text-primary)'
                    : 'var(--text-muted)',
                  fontWeight: isCurrent ? 500 : 400,
                }}>
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {isFailed && job.error && (
        <div className="p-3 rounded-xl text-sm"
          style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#FCA5A5' }}>
          <strong>Error:</strong> {friendlyProcessingError(job.error)}
        </div>
      )}
    </div>
  );
}
