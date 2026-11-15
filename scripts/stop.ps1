param([switch]$Docker)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($Docker) {
    & 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' compose stop
} else {
    foreach ($name in @('api','dashboard')) {
        $pidFile = Join-Path $PWD ".local\$name.pid"
        if (Test-Path -LiteralPath $pidFile) {
            $taskProcessId = [int](Get-Content -LiteralPath $pidFile)
            $taskProcess = Get-Process -Id $taskProcessId -ErrorAction SilentlyContinue
            if ($taskProcess -and $taskProcess.Path -like "$PWD\.venv\*") {
                # Windows venv launchers own a child Python process; stop the verified owned tree.
                & taskkill.exe /PID $taskProcessId /T /F | Out-Null
                if ($LASTEXITCODE) { throw "Could not stop owned $name process tree" }
            }
            Remove-Item -LiteralPath $pidFile
        }
    }
    if (Select-String -LiteralPath '.env' -Pattern '^DATABASE_URL=postgresql\+psycopg://commerce:.*@127\.0\.0\.1:5433/commerce$' -Quiet) {
        & '.\.venv\Scripts\python.exe' scripts/postgres_local.py stop
        if ($LASTEXITCODE) { throw 'Workspace PostgreSQL shutdown failed' }
    }
}
