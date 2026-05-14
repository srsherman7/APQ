# start.ps1 — Start the AWS Exam Practice App (backend + frontend)
# Supports both localhost and LAN/external access automatically.
# Run from the repo root: .\start.ps1

param(
    [string]$BindIP = "",                    # Override IP:  .\start.ps1 -BindIP 192.168.1.50
    [string]$PublicHost = ""                 # Override host: .\start.ps1 -PublicHost asjellyfin.tplinkdns.com
)

$Root     = $PSScriptRoot
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$EnvFile  = Join-Path $Frontend "src\environments\environment.ts"

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

$BackendUrl  = "http://${BindIP}:4201"
$FrontendUrl = "http://${BindIP}:4200"

# If a public hostname was supplied, use it for the API URL so external
# browsers can reach the backend (e.g. via DDNS / port forwarding).
if ($PublicHost -ne "") {
    $ApiUrl = "http://${PublicHost}:4201"
} else {
    $ApiUrl = $BackendUrl
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AWS Exam Practice App — Starting Up"   -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Host IP  : $BindIP"                    -ForegroundColor White
Write-Host "  Backend  : $BackendUrl"                -ForegroundColor Green
Write-Host "  Frontend : $FrontendUrl"               -ForegroundColor Green
if ($PublicHost -ne "") {
    Write-Host "  Public   : http://${PublicHost}:4200"  -ForegroundColor Yellow
}
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

# ── 5. Init DB + seed questions ───────────────────────────────────────────────
Write-Host "[3/5] Initialising database and seeding questions..." -ForegroundColor Yellow
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

# ── 6. Write environment.ts with the correct API URL ─────────────────────────
Write-Host "[4/5] Configuring frontend API URL -> $ApiUrl/api ..." -ForegroundColor Yellow
@"
// Auto-generated by start.ps1 — do not edit manually.
export const environment = {
  production: false,
  apiBaseUrl: '$ApiUrl/api'
};
"@ | Set-Content -Path $EnvFile -Encoding UTF8
Write-Host "      OK" -ForegroundColor Green

# ── 7. Launch backend ─────────────────────────────────────────────────────────
Write-Host "[5/5] Launching backend and frontend..." -ForegroundColor Yellow

$BackendCmd = @"
cd '$Backend'
`$env:CORS_ORIGINS = 'http://localhost:4200,http://${BindIP}:4200'
if ('$PublicHost' -ne '') {
    `$env:CORS_ORIGINS += ',http://${PublicHost}:4200'
}
Write-Host ''
Write-Host 'Backend running on $BackendUrl' -ForegroundColor Cyan
Write-Host 'CORS origins: ' + `$env:CORS_ORIGINS -ForegroundColor DarkGray
Write-Host ''
python app.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd

# ── 8. Launch frontend ────────────────────────────────────────────────────────
# --host 0.0.0.0 makes ng serve listen on all interfaces (LAN + localhost)
$FrontendCmd = @"
cd '$Frontend'
Write-Host ''
Write-Host 'Frontend running on $FrontendUrl' -ForegroundColor Cyan
Write-Host ''
npx ng serve --host 0.0.0.0 --port 4200 --allowed-hosts all --configuration development
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Two terminal windows have opened."     -ForegroundColor White
Write-Host "  Wait ~15s for Angular to compile."     -ForegroundColor White
Write-Host ""
Write-Host "  Local   : http://localhost:4200"       -ForegroundColor Green
Write-Host "  Network : $FrontendUrl"                -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
