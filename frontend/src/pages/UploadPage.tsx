import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowLeft, Loader2 } from 'lucide-react';
import { UploadZone } from '../components/Upload/UploadZone';
import { ProcessingStatus } from '../components/Upload/ProcessingStatus';
import { getApiError, uploadPodcast } from '../services/api';
import { useJobPoller } from '../hooks/useJobPoller';
import toast from 'react-hot-toast';

type Phase = 'idle' | 'uploading' | 'processing' | 'done';

export function UploadPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('idle');
  const [uploadPct, setUploadPct] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [podcastId, setPodcastId] = useState<string | null>(null);
  const [filename, setFilename] = useState('');
  const { job, error: pollError } = useJobPoller(jobId);

  // Auto navigate when done
  React.useEffect(() => {
    if (job?.stage === 'completed' && podcastId) {
      toast.success('Processing complete! Redirecting…');
      setTimeout(() => navigate(`/podcasts/${podcastId}`), 1200);
    }
    if (job?.stage === 'failed') {
      toast.error('Processing failed. See status for details.');
    }
  }, [job?.stage, podcastId, navigate]);

  const handleFile = async (file: File) => {
    setFilename(file.name);
    setPhase('uploading');
    try {
      const res = await uploadPodcast(file, (pct) => setUploadPct(pct));
      setJobId(res.job_id);
      setPodcastId(res.podcast_id);
      setPhase('processing');
      toast.success('Upload successful! AI processing started.');
    } catch (err: unknown) {
      toast.error(getApiError(err, 'Upload failed'));
      setPhase('idle');
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-slide-up">
      {/* Back button */}
      <button onClick={() => navigate('/')}
        className="flex items-center gap-2 text-sm transition-colors hover:opacity-70"
        style={{ color: 'var(--text-secondary)' }}>
        <ArrowLeft size={15} />
        Back to Dashboard
      </button>

      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Sparkles size={16} style={{ color: 'var(--accent-purple)' }} />
          <span className="text-sm font-medium" style={{ color: 'var(--accent-violet)' }}>
            AI-Powered Processing
          </span>
        </div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
          Upload Podcast
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          Upload your audio file and our AI pipeline will transcribe, segment, and summarize it.
        </p>
      </div>

      {/* Pipeline explanation */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[
          { step: '01', label: 'Whisper ASR', desc: 'Fast CPU speech-to-text transcription' },
          { step: '02', label: 'Topic groups', desc: 'Build navigable sections from the transcript' },
          { step: '03', label: 'Chapter highlights', desc: 'Create concise notes without a model download' },
        ].map(({ step, label, desc }) => (
          <div key={step} className="p-4 rounded-xl"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="text-xs font-mono mb-1" style={{ color: 'var(--accent-purple)' }}>{step}</div>
            <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{label}</div>
            <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{desc}</div>
          </div>
        ))}
      </div>

      {/* Upload area or status */}
      {phase === 'idle' && (
        <UploadZone onFile={handleFile} />
      )}

      {phase === 'uploading' && (
        <div className="rounded-2xl p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>
            Uploading {filename}…
          </p>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <div className="h-full rounded-full transition-all"
              style={{ width: `${uploadPct}%`, background: 'var(--gradient-primary)' }} />
          </div>
          <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>{uploadPct}% uploaded</p>
        </div>
      )}

      {phase === 'processing' && (job ? <ProcessingStatus job={job} filename={filename} connectionError={pollError} /> : (
        <div className="surface-card flex items-center gap-4 rounded-2xl p-5">
          <Loader2 size={20} className="animate-spin" style={{ color: 'var(--accent-purple)' }} />
          <div><p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{pollError ? 'Can’t reach the processing service' : 'Preparing your episode'}</p><p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>{pollError || 'Your upload is saved. Waiting for the job status…'}</p></div>
        </div>
      ))}

      {phase === 'processing' && job?.stage === 'failed' && (
        <div className="-mt-3 flex justify-end"><button onClick={() => { setJobId(null); setPodcastId(null); setPhase('idle'); setUploadPct(0); }} className="rounded-lg px-3 py-2 text-sm font-semibold" style={{ background: '#fff0ed', color: '#a64f40' }}>Choose another file</button></div>
      )}

      {/* Info note */}
      <div className="px-4 py-3 rounded-xl text-sm"
        style={{ background: 'rgba(34,211,238,0.06)', border: '1px solid rgba(34,211,238,0.15)', color: 'var(--text-secondary)' }}>
        <strong style={{ color: 'var(--accent-violet)' }}>Fast mode is on:</strong> Whisper uses quick decoding, topic sections are grouped from the transcript,
        and chapter highlights are created locally. This avoids large downloads and is much faster on CPU.
      </div>
    </div>
  );
}
