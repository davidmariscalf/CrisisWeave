param([string]$WorkDir = "./crisisweave-demo")
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
Set-Location $WorkDir

function Clone-Or-Update([string]$Repo) {
  if (Test-Path "$Repo/.git") {
    git -C $Repo pull --ff-only
  } else {
    git clone "https://github.com/davidmariscalf/$Repo.git"
  }
}

Clone-Or-Update "crisisweave-sim"
Clone-Or-Update "crisisweave-verify"
Clone-Or-Update "crisisweave-alerts"

python crisisweave-sim/simulate.py --scenario mixed --count 30 --seed 42 | Out-File -Encoding utf8 events.jsonl
Get-Content events.jsonl | python crisisweave-verify/verifier.py | Out-File -Encoding utf8 verified.jsonl

@'
[
  {
    "id": "high-severity-flood",
    "kinds": ["flood"],
    "min_severity": 0.7,
    "min_confidence": 0.7
  },
  {
    "id": "high-severity-wildfire",
    "kinds": ["wildfire"],
    "min_severity": 0.75,
    "min_confidence": 0.7
  }
]
'@ | Out-File -Encoding utf8 rules.json

Get-Content verified.jsonl | python crisisweave-alerts/alerts.py rules.json | Out-File -Encoding utf8 alerts.jsonl

$rawCount = (Get-Content events.jsonl).Count
$verifiedCount = (Get-Content verified.jsonl).Count
$alertCount = (Get-Content alerts.jsonl).Count
Write-Host ""
Write-Host "CrisisWeave demo complete."
Write-Host "Raw events:      $rawCount"
Write-Host "Verified events: $verifiedCount"
Write-Host "Alert matches:   $alertCount"
Write-Host "Open verified.jsonl in crisisweave-map to inspect mapped events."
