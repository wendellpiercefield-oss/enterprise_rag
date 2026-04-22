$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Run .\setup.ps1 first."
}

& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000 --app-dir backend

#cd 'E:\AI System\knowledge-platform'
#.\backend\.venv\Scripts\activate
#python -m uvicorn app.main:app --port 8000