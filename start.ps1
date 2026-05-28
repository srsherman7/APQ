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
python -m pip install -r (Join-Path $Backend "requirements.txt") -q
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
$LASTEXITCODE = 0
node node_modules\@angular\cli\bin\ng.js build --configuration production 2>&1 | Tee-Object -Variable buildOutput | Select-String -Pattern "error|complete|failed" -CaseSensitive:$false
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
from models.module import Module
from models.question import Question

app = create_app()
with app.app_context():
    db.create_all()
    
    # Create Cloud Practitioner module if it doesn't exist
    module = Module.query.filter_by(slug='cloud-practitioner').first()
    if not module:
        module = Module(
            slug='cloud-practitioner',
            name='AWS Cloud Practitioner',
            description='Prepare for the AWS Certified Cloud Practitioner exam. Covers cloud concepts, security, technology, and billing.',
            icon='cloud',
            exam_question_count=65,
            exam_time_limit_seconds=5400,
            exam_passing_score=70.0,
            topic_areas=['Cloud Concepts', 'Security and Compliance', 'Technology', 'Billing and Pricing'],
        )
        db.session.add(module)
        db.session.commit()
        print(f'  Created module: {module.name}')
    
    # Seed questions into the module
    seed_path = os.path.join(r'$Backend', 'seed_data', 'questions.json')
    with open(seed_path, encoding='utf-8') as f:
        questions = json.load(f)
    count = 0
    for q in questions:
        if not Question.query.filter_by(question_text=q['question_text']).first():
            db.session.add(Question(
                module_id=module.module_id,
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
    total = Question.query.filter_by(is_active=True).count()
    print(f'  Seeded {count} new questions. Total active: {total}')
    
    # Create ML Specialty module if it doesn't exist
    ml_module = Module.query.filter_by(slug='ml-specialty').first()
    if not ml_module:
        ml_module = Module(
            slug='ml-specialty',
            name='AWS Machine Learning Specialty',
            description='Prepare for the AWS Certified Machine Learning - Specialty exam. Covers data engineering, EDA, modeling, and ML ops.',
            icon='psychology',
            exam_question_count=85,
            exam_time_limit_seconds=10200,
            exam_passing_score=75.0,
            topic_areas=['Data Engineering', 'Exploratory Data Analysis', 'Modeling', 'ML Implementation and Operations'],
        )
        db.session.add(ml_module)
        db.session.commit()
        print(f'  Created module: {ml_module.name}')
    
    # Seed ML questions
    import os as _os
    ml_seed = _os.path.join(r'$Backend', 'seed_data', 'ml_questions.json')
    if _os.path.exists(ml_seed):
        with open(ml_seed, encoding='utf-8') as f:
            ml_qs = json.load(f)
        ml_count = 0
        for q in ml_qs:
            if not Question.query.filter_by(question_text=q['question_text']).first():
                db.session.add(Question(
                    module_id=ml_module.module_id,
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
                ml_count += 1
        db.session.commit()
        if ml_count > 0:
            print(f'  Seeded {ml_count} ML questions')
    
    # Create Developer Associate module if it doesn't exist
    dva_module = Module.query.filter_by(slug='developer-associate').first()
    if not dva_module:
        dva_module = Module(
            slug='developer-associate',
            name='AWS Developer Associate',
            description='Prepare for the AWS Certified Developer - Associate exam. Covers development with AWS services, security, deployment, and troubleshooting.',
            icon='code',
            exam_question_count=65,
            exam_time_limit_seconds=7800,
            exam_passing_score=72.0,
            topic_areas=['Development with AWS Services', 'Security', 'Deployment', 'Troubleshooting and Optimization'],
        )
        db.session.add(dva_module)
        db.session.commit()
        print(f'  Created module: {dva_module.name}')
    
    # Seed DVA questions
    dva_seed = _os.path.join(r'$Backend', 'seed_data', 'dva_questions.json')
    if _os.path.exists(dva_seed):
        with open(dva_seed, encoding='utf-8') as f:
            dva_qs = json.load(f)
        dva_count = 0
        for q in dva_qs:
            if not Question.query.filter_by(question_text=q['question_text']).first():
                db.session.add(Question(
                    module_id=dva_module.module_id,
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
                dva_count += 1
        db.session.commit()
        if dva_count > 0:
            print(f'  Seeded {dva_count} DVA questions')
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
