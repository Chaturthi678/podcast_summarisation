# Start Podly AI Frontend
Write-Host "Starting Podly AI Frontend..." -ForegroundColor Magenta
Set-Location "$PSScriptRoot\frontend"
npm run dev -- --host 0.0.0.0
