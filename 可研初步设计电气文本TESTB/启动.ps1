# PowerShell launcher - 双击运行
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$PythonPaths = @(
    "$env:USERPROFILE\.workbuddy\binaries\python\versions\3.13.12\python.exe",
    "$env:USERPROFILE\.workbuddy\binaries\python\versions\3.12.*\python.exe"
)

$Python = $null
foreach ($p in $PythonPaths) {
    $resolved = Resolve-Path $p -ErrorAction SilentlyContinue
    if ($resolved) { $Python = $resolved.Path; break }
}
if (-not $Python) { $Python = "python" }

Write-Host "Launching GUI with: $Python"
& $Python gui.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n=== Dependency check ===" -ForegroundColor Yellow
    & $Python -c "import tkinter" 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "MISSING: tkinter" -ForegroundColor Red }
    & $Python -c "import openpyxl" 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "MISSING: openpyxl" -ForegroundColor Red }
    & $Python -c "import xlrd" 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "MISSING: xlrd" -ForegroundColor Red }
    & $Python -c "from docx import Document" 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "MISSING: python-docx" -ForegroundColor Red }
    Read-Host "Press Enter to exit"
}
