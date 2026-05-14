# start.ps1 — Build and start the AWS Exam Practice App
#
# Everything runs through a single port (4201).
# Flask serves both the API (/api/*) and the Angular production build.
#
# Usage:
#   .\start.ps1                  # auto-detect LAN IP
#   .\start.ps1 -BindIP 0.0.0.0  # listen on all interfaces

param(
    [string]$BindIP = ""
)

$Root     = $PSScriptRoot
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

# ── Detect LAN IP ─────────────────────────────────────────────────────────────
if ($BindIP -eq "") {
    $BindIP = (
        Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.|172\.)' } |
        Sort-Object PrefixLength -Descending |
        Select-Object -First 1 -ExpandProperty IPAddress
    )
    if (-not $BindIP) { $BindIP = "127.0.0.1" }
}

$AppUrl = "http://${BindIP}:4201"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AWS Exam Practice App — Starting Up"   -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  URL : $AppUrl"                         -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check Python ───────────────────────────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

# ── 2. Check Node / npm ───────────────────────────────────────────────────────
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] npm not found. Please install Node.js 18+." -ForegroundColor Red
    exit 1
}

# ── 3. Install Python dependencies ───────────────────────────────────────────
Write-Host "[1/5] Checking Python dependencies..." -ForegroundColor Yellow
pip install -r (Join-Path $Backend "requirements.txt") -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed." -ForegroundColor Red; exit 1
}
Write-Host "      OK" -ForegroundColor Green

# ── 4. Install Node dependencies ─────────────────────────────────────────────
$NodeModules = Join-Path $Frontend "node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Host "[2/5] Installing Node dependencies (first run)..." -ForegroundColor Yellow
    Push-Location $Frontend; npm install --silent; Pop-Location
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed." -ForegroundColor Red; exit 1
    }
} else {
    Write-Host "[2/5] Node dependencies already installed." -ForegroundColor Green
}

# ── 5. Build Angular for production ──────────────────────────────────────────
Write-Host "[3/5] Building Angular (production)..." -ForegroundColor Yellow
Push-Location $Frontend
npx ng build --configuration production 2>&1 | Tee-Object -Variable buildOutput | Select-String -Pattern "error|complete|failed" -CaseSensitive:$false
Pop-Location
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Angular build failed." -ForegroundColor Red; exit 1
}
Write-Host "      OK" -ForegroundColor Green

# ── 6. Init DB + seed questions ───────────────────────────────────────────────
Write-Host "[4/5] Initialising database and seeding questions..." -ForegroundColor Yellow
$InitScript = @"
import json, os, sys
sys.path.insert(0, r'$Backend')
os.chdir(r'$Backend')
from app import create_app
from extensions import db
from models.question import Question

app = create_app()
with app.app_context():
    db.create_all()
    seed_path = os.path.join(r'$Backend', 'seed_data', 'questions.json')
    with open(seed_path, encoding='utf-8') as f:
        questions = json.load(f)
    count = 0
    for q in questions:
        if not Question.query.filter_by(question_text=q['question_text']).first():
            db.session.add(Question(
                question_text=q['question_text'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                explanation=q['explanation'],
                memory_technique=q['memory_technique'],
                topic_area=q['topic_area'],
                difficulty_level=q['difficulty_level'],
                it_context_mapping=q.get('it_context_mapping'),
                is_active=True
            ))
            count += 1
    db.session.commit()
    total = Question.query.count()
    print(f'  Seeded {count} new questions. Total in DB: {total}')
"@
python -c $InitScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Database init failed." -ForegroundColor Red; exit 1
}
Write-Host "      OK" -ForegroundColor Green

# ── 7. Launch Flask (serves API + Angular static files) ───────────────────────
Write-Host "[5/5] Starting server..." -ForegroundColor Yellow

$ServerCmd = @"
cd '$Backend'
`$env:CORS_ORIGINS = 'http://localhost:4201,http://${BindIP}:4201'
Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  App running on $AppUrl' -ForegroundColor Green
Write-Host '  Also available on http://localhost:4201' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
try { python app.py } catch { Write-Host `$_.Exception.Message -ForegroundColor Red }
Write-Host 'Server stopped. Press Enter to close.' -ForegroundColor Yellow
Read-Host
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $ServerCmd

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Server starting in a new window."      -ForegroundColor White
Write-Host "  Open: $AppUrl"                         -ForegroundColor Green
Write-Host "  Also: http://localhost:4201"           -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
