param([switch]$ConfirmLocalReset)
$ErrorActionPreference = 'Stop'
$rootPath = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
if (!$ConfirmLocalReset) { throw 'Reset removes generated SQLite warehouse/artifacts. Rerun with -ConfirmLocalReset only if intended.' }
& (Join-Path $PSScriptRoot 'stop.ps1')
foreach ($relativePath in @('data\warehouse','artifacts')) {
    $targetPath = [IO.Path]::GetFullPath((Join-Path $rootPath $relativePath))
    if (!$targetPath.StartsWith($rootPath + [IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe reset target' }
    if (Test-Path -LiteralPath $targetPath) { Remove-Item -LiteralPath $targetPath -Recurse -Force }
}
Write-Output 'Generated local warehouse/artifacts removed. Source data and .env retained. Docker volumes retained.'
