param([switch]$Docker)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($Docker) {
    $dockerExe = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
    if (!(Test-Path -LiteralPath $dockerExe)) { $dockerExe = 'docker' }
    & $dockerExe compose up -d --build
    if ($LASTEXITCODE) { throw 'Compose startup failed' }
} else {
    New-Item -ItemType Directory -Path '.local' -Force | Out-Null
    $python = Join-Path $PWD '.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $python)) { throw 'Run scripts/setup.ps1 first' }
    if (Select-String -LiteralPath '.env' -Pattern '^DATABASE_URL=postgresql\+psycopg://commerce:.*@127\.0\.0\.1:5433/commerce$' -Quiet) {
        & $python scripts/postgres_local.py start
        if ($LASTEXITCODE) { throw 'Workspace PostgreSQL startup failed' }
    }
    $jobs = @(
        @{Name='api'; Port=8000; Arguments=@('-m','uvicorn','commerce.api:app','--host','127.0.0.1','--port','8000')},
        @{Name='dashboard'; Port=8501; Arguments=@('-m','streamlit','run','app/dashboard.py')}
    )
    foreach ($job in $jobs) {
        $pidFile = Join-Path $PWD ".local\$($job.Name).pid"
        if (Test-Path -LiteralPath $pidFile) {
            $oldId = [int](Get-Content -LiteralPath $pidFile)
            $oldProcess = Get-Process -Id $oldId -ErrorAction SilentlyContinue
            if ($oldProcess) {
                if ($oldProcess.Path -like "$PWD\.venv\*") { continue }
                throw "Saved $($job.Name) PID belongs to another process; refusing to use it"
            }
        }
        $portClient = New-Object Net.Sockets.TcpClient
        $portInUse = $false
        try { $portClient.Connect('127.0.0.1', $job.Port); $portInUse = $true } catch {} finally { $portClient.Dispose() }
        if ($portInUse) { throw "Port $($job.Port) is already in use without an owned process record" }
        $process = Start-Process -FilePath $python -ArgumentList $job.Arguments -WorkingDirectory $PWD -WindowStyle Hidden -PassThru -RedirectStandardOutput ".local\$($job.Name).stdout.log" -RedirectStandardError ".local\$($job.Name).stderr.log"
        Set-Content -LiteralPath $pidFile -Value $process.Id
    }
}
$ready = $false
for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try {
        $api = Invoke-RestMethod 'http://127.0.0.1:8000/ready' -TimeoutSec 3
        $ui = Invoke-WebRequest 'http://127.0.0.1:8501/_stcore/health' -TimeoutSec 3 -UseBasicParsing
        if ($api.status -eq 'ready' -and $ui.StatusCode -eq 200) { $ready = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if (!$ready) { throw 'Startup health verification failed; inspect .local logs or docker compose logs' }
Write-Output 'Verified: http://127.0.0.1:8501 | API docs: http://127.0.0.1:8000/docs'
