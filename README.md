# Podly AI — Podcast Summariser & Chapter Generator

A complete, AI-powered podcast analysis application that transcribes audio, detects topics, generates chapter summaries, and exports ID3 chapter metadata.

## 🤖 AI Pipeline
1. **Faster-Whisper ASR** — Timestamped speech-to-text using CTranslate2 and int8 CPU inference by default; OpenAI Whisper remains available as a fallback engine
2. **Fast mode (default)** — Tiny Whisper, lightweight topic grouping, and extractive chapter highlights
3. **Deep analysis (optional)** — BERTopic clustering and DistilBART summaries (`FAST_PROCESSING=false`)
4. **Mutagen** — ID3 CHAP frame metadata written to MP3

## 📋 Requirements

| Dependency | Version |
|---|---|
| Python | 3.11+ (3.14 tested) |
| Node.js | 18+ |
| FFmpeg | Auto-downloaded via imageio-ffmpeg |
| RAM | 4GB+ recommended (8GB for medium Whisper model) |

---

## 🚀 Quick Start

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Note:** This will download PyTorch (~2GB) and AI model weights (~500MB) on first run.

### 2. Start the Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/api/docs

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at: http://localhost:5173

---

## 📁 Project Structure

```
podcast_summarisation_project/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry point
│   │   ├── config.py            ← Settings & env vars
│   │   ├── database.py          ← SQLAlchemy models
│   │   ├── schemas.py           ← Pydantic API schemas
│   │   ├── api/
│   │   │   ├── podcasts.py      ← Podcast endpoints
│   │   │   └── jobs.py          ← Job status endpoint
│   │   ├── services/
│   │   │   ├── audio.py         ← Mutagen + bundled FFmpeg
│   │   │   ├── transcription.py ← Whisper ASR
│   │   │   ├── topic_detection.py ← BERTopic
│   │   │   ├── summarization.py ← DistilBART
│   │   │   ├── metadata.py      ← Mutagen ID3 CHAP frames
│   │   │   └── export.py        ← TXT/MD/JSON/MP3 exports
│   │   └── workers/
│   │       └── processing.py    ← Background job executor
│   ├── uploads/                 ← Uploaded audio files
│   ├── outputs/                 ← Generated exports per podcast
│   └── requirements.txt
└── frontend/
    └── src/
        ├── components/          ← Reusable UI components
        ├── pages/               ← Route-level pages
        ├── services/api.ts      ← Axios API client
        ├── hooks/               ← React hooks
        └── types/index.ts       ← TypeScript types
```

---

## ⚙️ Configuration

Edit `backend/.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `tiny` | ASR model size (tiny/base/small/medium/large) |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `TRANSCRIPTION_ENGINE` | `faster-whisper` | `faster-whisper` (int8 CPU) or `openai-whisper` |
| `SUMMARIZER_MODEL` | `sshleifer/distilbart-cnn-12-6` | HuggingFace model |
| `MAX_UPLOAD_SIZE_MB` | `500` | Upload limit in MB |
| `FAST_PROCESSING` | `true` | Use the quicker topic and summary pipeline |
| `PROCESSING_WORKERS` | `1` | Concurrent local analysis jobs; raise only when hardware has spare memory/compute |

---

Fast mode is the default. It uses cached Whisper Tiny weights when available, skips temporary WAV creation and word alignment, groups transcript topics locally, and creates chapter highlights without downloading a summarizer. This machine processed the included 2m41s speech sample in about 18 seconds after model setup. Actual time varies with CPU and audio quality.

Set `FAST_PROCESSING=false` in `backend/.env` to enable the heavier BERTopic and DistilBART pipeline. Those models may require additional downloads and take longer on CPU.

Uploads are streamed to disk, episode detail responses stay small (transcripts load from their own endpoint), the library is paged, and SQLite query paths are indexed. The bundled worker uses an in-process thread pool; queued work is not durable across a backend restart, so run one backend process for local use. For multi-instance production use, move job execution to a durable shared queue such as Redis/Celery or a managed task service and use PostgreSQL plus shared object storage; do not scale the in-process thread pool across multiple API instances.

---

## 🛠️ Troubleshooting

**Backend won't start:**
```bash
pip install -r requirements.txt
python -c "import fastapi, whisper, bertopic; print('OK')"
```

**FFmpeg errors:**
```bash
python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
```
`imageio-ffmpeg` downloads the binary automatically to a cache directory.

**PyTorch not found:**
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**Models downloading slowly:**
Models are cached after first download in `~/.cache/huggingface/`.

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/podcasts/upload` | POST | Upload audio file |
| `/api/jobs/{job_id}` | GET | Poll job status |
| `/api/podcasts` | GET | List all podcasts |
| `/api/podcasts/{id}` | GET | Get podcast details |
| `/api/podcasts/{id}/transcript` | GET | Get transcript |
| `/api/podcasts/{id}/chapters` | GET | Get chapters |
| `/api/podcasts/{id}/chapters/{cid}` | PATCH | Edit chapter |
| `/api/podcasts/{id}/download/{fmt}` | GET | Download (txt/md/json/mp3) |
| `/api/podcasts/{id}/audio` | GET | Stream audio |
