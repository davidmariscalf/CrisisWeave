param(
  [string]$WorkDir = ".\crisisweave-demo"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
  $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
  throw "Python 3 is required."
}

& $python.Source "$ScriptDir\production_check.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python.Source "$ScriptDir\run_pinned.py" --workspace $WorkDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "CrisisWeave locked E2E artifact created in: $WorkDir\artifact"
Write-Host "Verify the sealed artifact with:"
Write-Host "  python $ScriptDir\seal_artifact.py $WorkDir\artifact --verify"
Write-Host "To inspect the field console:"
Write-Host "  cd $WorkDir\artifact"
Write-Host "  python -m http.server 8765 -d web"
Write-Host "  http://localhost:8765/index.html"
