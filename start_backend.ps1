# Start Podly AI Backend
Write-Host "Starting Podly AI Backend..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\backend"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
