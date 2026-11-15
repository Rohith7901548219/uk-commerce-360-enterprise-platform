param([switch]$Services)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($Services -and (!$env:SERVICE_DATABASE_URL -or !$env:SERVICE_KAFKA_BOOTSTRAP_SERVERS)) {
    throw 'Service verification requires an isolated SERVICE_DATABASE_URL and SERVICE_KAFKA_BOOTSTRAP_SERVERS; refusing to report skipped services as verified'
}
& '.\.venv\Scripts\ruff.exe' check .
if ($LASTEXITCODE) { throw 'Lint failed' }
$testArguments = @('-m','pytest','--junitxml=artifacts/tests.xml')
if (!$Services) { $testArguments += @('-m','not services') }
& '.\.venv\Scripts\python.exe' @testArguments
if ($LASTEXITCODE) { throw 'Tests failed' }
