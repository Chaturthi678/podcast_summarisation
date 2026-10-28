import { useState, useEffect } from 'react';
import { getJobStatus } from '../services/api';
import type { JobStatus } from '../types';

export function useJobPoller(jobId: string | null, interval = 2000) {
  const [state, setState] = useState<{ jobId: string | null; job: JobStatus | null; error: string | null }>({ jobId: null, job: null, error: null });

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let delay = interval;
    if (!jobId) return;

    const poll = async () => {
      try {
        const status = await getJobStatus(jobId);
        if (cancelled) return;
        setState({ jobId, job: status, error: null });
        delay = interval;
        if (status.stage === 'completed' || status.stage === 'failed') return;
      } catch (err: unknown) {
        if (cancelled) return;
        setState(current => ({ jobId, job: current.jobId === jobId ? current.job : null, error: err instanceof Error ? err.message : 'Could not refresh processing status.' }));
        delay = Math.min(Math.round(delay * 1.6), 12000);
      }
      if (!cancelled) timer = setTimeout(poll, delay);
    };

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [jobId, interval]);

  return {
    job: state.jobId === jobId ? state.job : null,
    error: state.jobId === jobId ? state.error : null,
  };
}
