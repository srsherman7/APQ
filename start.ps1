# start.ps1 — Start the AWS Exam Practice App (backend + frontend)
# Run from the repo root: .\start.ps1

$Root    = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AWS Exam Practice App — Starting Up"   -ForegroundColor Cyan
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

# ── 3. Install Python dependencies if needed ─────────────────────────────────
$ReqFile = Join-Path $Backend "requirements.txt"
Write-Host "[1/4] Checking Python dependencies..." -ForegroundColor Yellow
pip install -r $ReqFile -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed." -ForegroundColor Red
    exit 1
}
Write-Host "      OK" -ForegroundColor Green

# ── 4. Install Node dependencies if needed ───────────────────────────────────
$NodeModules = Join-Path $Frontend "node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Host "[2/4] Installing Node dependencies (first run)..." -ForegroundColor Yellow
    Push-Location $Frontend
    npm install --silent
    Pop-Location
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[2/4] Node dependencies already installed." -ForegroundColor Green
}

# ── 5. Init DB + seed questions ───────────────────────────────────────────────
Write-Host "[3/4] Initialising database and seeding questions..." -ForegroundColor Yellow
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
    Write-Host "[ERROR] Database init failed." -ForegroundColor Red
    exit 1
}
Write-Host "      OK" -ForegroundColor Green

# ── 6. Launch backend in a new window ────────────────────────────────────────
Write-Host "[4/4] Starting backend and frontend..." -ForegroundColor Yellow
Write-Host ""

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Backend'; Write-Host 'Backend running on http://localhost:5000' -ForegroundColor Cyan; python app.py"
)

# ── 7. Launch frontend in a new window ───────────────────────────────────────
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Frontend'; Write-Host 'Frontend running on http://localhost:4200' -ForegroundColor Cyan; npm start"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Backend  -> http://localhost:5000"      -ForegroundColor Green
Write-Host "  Frontend -> http://localhost:4200"      -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Two terminal windows have opened." -ForegroundColor White
Write-Host "Wait ~10 seconds for the frontend to compile, then open:" -ForegroundColor White
Write-Host "  http://localhost:4200" -ForegroundColor Yellow
Write-Host ""
