param([switch]$SkipData, [switch]$UseMirror)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.tools\python"
$env:UV_CACHE_DIR = "$PWD\.tools\clean-cache"
$uv = Join-Path $PWD '.tools\uv\uv.exe'
if (!(Test-Path -LiteralPath $uv)) {
    New-Item -ItemType Directory -Path '.tools' -Force | Out-Null
    Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/download/0.13.8/uv-x86_64-pc-windows-msvc.zip' -OutFile '.tools\uv.zip'
    Expand-Archive -LiteralPath '.tools\uv.zip' -DestinationPath '.tools\uv' -Force
}
& $uv python install 3.12
if ($LASTEXITCODE) { throw 'Python installation failed' }
& $uv sync --frozen --extra dev --extra warehouse
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
& '.\.venv\Scripts\python.exe' -m commerce.cli bootstrap
& '.\.venv\Scripts\alembic.exe' upgrade head
if ($LASTEXITCODE) { throw 'Migration failed' }
if (!$SkipData) {
    if ($UseMirror) {
        $envContent = Get-Content -LiteralPath '.env' -Raw
        if ($envContent -match '(?m)^DATA_ACQUISITION=') {
            $envContent = $envContent -replace '(?m)^DATA_ACQUISITION=.*$', 'DATA_ACQUISITION=mirror'
        } else { $envContent += "`nDATA_ACQUISITION=mirror`n" }
        Set-Content -LiteralPath '.env' -Value $envContent -Encoding UTF8
        & '.\.venv\Scripts\python.exe' scripts/acquire_mirror.py
        if ($LASTEXITCODE) { throw 'Mirror acquisition failed' }
        & '.\.venv\Scripts\python.exe' -m commerce.cli pipeline --path data/raw/online_retail_II.mirror.xlsx --mirrored
    } else {
        & '.\.venv\Scripts\python.exe' -m commerce.cli pipeline
    }
    if ($LASTEXITCODE) { throw 'Data acquisition or pipeline failed; inspect PROGRESS.md' }
    & '.\.venv\Scripts\python.exe' -m commerce.cli train
    if ($LASTEXITCODE) { throw 'Model training failed' }
}
Write-Output 'Setup complete. Run .\scripts\start.ps1'
