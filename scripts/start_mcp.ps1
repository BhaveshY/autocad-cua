$ErrorActionPreference='Stop'
$probe = (& (Join-Path $PSScriptRoot 'doctor.ps1') | Out-String) | ConvertFrom-Json
if(-not $probe.prerequisites_ready){throw 'AutoCAD Cua prerequisites are unavailable.'}
$env:PYTHONIOENCODING='utf-8'
& $probe.python -u (Join-Path $PSScriptRoot 'mcp_server.py')
exit $LASTEXITCODE
