import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Layout } from './components/Layout/Layout';

const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));
const UploadPage = lazy(() => import('./pages/UploadPage').then(module => ({ default: module.UploadPage })));
const PodcastsPage = lazy(() => import('./pages/PodcastsPage').then(module => ({ default: module.PodcastsPage })));
const PodcastAnalysis = lazy(() => import('./pages/PodcastAnalysis').then(module => ({ default: module.PodcastAnalysis })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(module => ({ default: module.SettingsPage })));

function PageLoading() {
  return <div className="surface-card flex min-h-48 items-center justify-center rounded-2xl text-sm" style={{ color: 'var(--text-muted)' }}>Opening your workspace…</div>;
}

export default function App() {
  return <BrowserRouter>
    <Toaster position="top-right" toastOptions={{ style: { background: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border-accent)', borderRadius: 12, fontFamily: 'Inter, sans-serif', fontSize: 14 }, success: { iconTheme: { primary: '#39866e', secondary: 'var(--bg-card)' } }, error: { iconTheme: { primary: '#b55342', secondary: 'var(--bg-card)' } } }} />
    <Suspense fallback={<PageLoading />}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/podcasts" element={<PodcastsPage />} />
          <Route path="/podcasts/:id" element={<PodcastAnalysis />} />
          <Route path="/transcripts" element={<Navigate to="/podcasts?view=transcripts" replace />} />
          <Route path="/chapters" element={<Navigate to="/podcasts?view=chapters" replace />} />
          <Route path="/exports" element={<Navigate to="/podcasts?view=exports" replace />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  </BrowserRouter>;
}
