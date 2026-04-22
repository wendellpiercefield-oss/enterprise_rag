param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$VenvPath = ".venv",
    [string]$PythonCmd = "python",
    [string]$RequirementsFile = "requirements.txt",
    [string]$PostgresContainer = "kp-postgres",
    [string]$PostgresDb = "knowledge",
    [string]$PostgresUser = "knowledge",
    [string]$EmbedModel = "nomic-embed-text",
    [string]$LlmModel = "gpt-oss:20b"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "  OK  $msg" -ForegroundColor Green
}

function Write-WarnMsg($msg) {
    Write-Host "  WARN $msg" -ForegroundColor Yellow
}

function Write-Fail($msg) {
    Write-Host "  FAIL $msg" -ForegroundColor Red
}

function Test-CommandExists($name) {
    return $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

Set-Location $ProjectRoot

Write-Step "Project root"
Write-Ok (Get-Location).Path

# -----------------------------
# ENV file
# -----------------------------
Write-Step "Checking .env configuration"

if (-not (Test-Path ".env")) {

    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env" -Force:$false
        Write-Ok "Created .env from .env.example"
    }
    else {
        Write-WarnMsg ".env.example not found. Skipping .env creation."
    }

}
else {
    Write-Ok ".env already exists"
}

# -----------------------------
# Python / venv
# -----------------------------
Write-Step "Checking Python"

if (-not (Test-CommandExists $PythonCmd)) {
    throw "Python command '$PythonCmd' not found in PATH."
}

$pythonVersion = & $PythonCmd --version
Write-Ok $pythonVersion

if (-not (Test-Path $VenvPath)) {
    Write-Step "Creating virtual environment"
    & $PythonCmd -m venv $VenvPath
    Write-Ok "Created $VenvPath"
}
else {
    Write-Ok "Virtual environment already exists"
}

$venvPython = Join-Path $VenvPath "Scripts\python.exe"
$venvPip = Join-Path $VenvPath "Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python not found at $venvPython"
}

Write-Step "Installing Python dependencies"

if (-not (Test-Path $RequirementsFile)) {
    throw "Missing $RequirementsFile in repo root."
}

& $venvPython -m pip install --upgrade pip
& $venvPip install -r $RequirementsFile
Write-Ok "Dependencies installed"

# -----------------------------
# Runtime folders
# -----------------------------
Write-Step "Creating runtime folders"

$folders = @(
    "data",
    "data\files",
    "uploads",
    "logs"
)

foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Ok "Created $folder"
    }
    else {
        Write-Ok "$folder already exists"
    }
}

# -----------------------------
# Docker / Postgres
# -----------------------------
Write-Step "Checking Docker"

if (-not (Test-CommandExists "docker")) {
    Write-WarnMsg "Docker not found. Skipping Postgres startup/bootstrap."
}
else {
    $dockerVersion = docker --version
    Write-Ok $dockerVersion

    $containerExists = docker ps -a --format "{{.Names}}" | Select-String -SimpleMatch $PostgresContainer

    if ($containerExists) {
        Write-Step "Ensuring Postgres container is running"
        docker start $PostgresContainer | Out-Null
        Write-Ok "$PostgresContainer is running"

        Start-Sleep -Seconds 3

        Write-Step "Ensuring pgvector extension exists"
        docker exec $PostgresContainer psql -U $PostgresUser -d $PostgresDb -c "CREATE EXTENSION IF NOT EXISTS vector;" | Out-Null
        Write-Ok "pgvector extension checked"

        # optional bootstrap sql
        $sqlCandidates = @(
            "backend\app\database\init.sql",
            "backend\database\init.sql",
            "database\init.sql"
        )

        $sqlFile = $sqlCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

        if ($sqlFile) {
            Write-Step "Running bootstrap SQL from $sqlFile"
            Get-Content $sqlFile -Raw | docker exec -i $PostgresContainer psql -U $PostgresUser -d $PostgresDb | Out-Null
            Write-Ok "Bootstrap SQL applied"
        }
        else {
            Write-WarnMsg "No init.sql found. Skipping schema bootstrap."
        }
    }
    else {
        Write-WarnMsg "Container '$PostgresContainer' not found. Skipping Postgres startup/bootstrap."
    }
}

# -----------------------------
# Ollama
# -----------------------------
Write-Step "Checking Ollama"

if (-not (Test-CommandExists "ollama")) {
    Write-WarnMsg "Ollama not found in PATH. Install Ollama before running chat/embedding features."
}
else {
    $ollamaVersion = ollama --version
    Write-Ok $ollamaVersion

    $ollamaList = ollama list 2>$null

    if ($ollamaList -match [regex]::Escape($EmbedModel)) {
        Write-Ok "Embedding model present: $EmbedModel"
    }
    else {
        Write-WarnMsg "Embedding model missing: $EmbedModel"
        Write-Host "       Run: ollama pull $EmbedModel"
    }

    if ($ollamaList -match [regex]::Escape($LlmModel)) {
        Write-Ok "LLM model present: $LlmModel"
    }
    else {
        Write-WarnMsg "LLM model missing: $LlmModel"
        Write-Host "       Run: ollama pull $LlmModel"
    }
}

# -----------------------------
# Final guidance
# -----------------------------
Write-Step "Setup complete"

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Activate venv:" -ForegroundColor Gray
Write-Host "   .\.venv\Scripts\Activate" -ForegroundColor White
Write-Host ""
Write-Host "2. Start API:" -ForegroundColor Gray
Write-Host "   .\run.ps1" -ForegroundColor White
Write-Host ""
Write-Host "3. Open UI:" -ForegroundColor Gray
Write-Host "   If using a static server for UI, serve the UI folder and browse to it." -ForegroundColor White