param([string]$PythonPath)
$ErrorActionPreference='Stop'
$pluginRoot=Split-Path $PSScriptRoot -Parent
$manifest=Get-Content -LiteralPath (Join-Path $pluginRoot 'runtime.json') -Raw|ConvertFrom-Json
$binary=Join-Path $pluginRoot 'bin\cua-driver.exe'
$windowsX64=[Environment]::OSVersion.Platform -eq 'Win32NT' -and $env:PROCESSOR_ARCHITECTURE -eq 'AMD64'
$stream=[IO.File]::OpenRead($binary)
$algorithm=[Security.Cryptography.SHA256]::Create()
try {$actualHash=[BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-','');$hashOkay=$actualHash -eq $manifest.sha256}
finally {$stream.Dispose();$algorithm.Dispose()}
$version=$null
if($windowsX64 -and $hashOkay){$version=(& $binary --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0){throw 'Driver version probe failed'}}
$candidates=@($PythonPath,$env:AUTOCAD_CUA_PYTHON)
$candidates+=@(Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE '.cache\codex-runtimes') -Directory -ErrorAction SilentlyContinue|ForEach-Object {Join-Path $_.FullName 'dependencies\python\python.exe'}|Where-Object {Test-Path -LiteralPath $_})
$candidates+=@(Get-Command python,python3 -ErrorAction SilentlyContinue|ForEach-Object Source)
$python=$null
foreach($candidate in $candidates|Where-Object {$_}|Select-Object -Unique){
 if($candidate -match '\\WindowsApps\\'){continue}
 try {
  $answer=& $candidate -c 'import sys; print(sys.executable); sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>$null
  if($LASTEXITCODE -eq 0){$python=([string]($answer|Select-Object -Last 1)).Trim();break}
 } catch {}
}
$progIds=@([Microsoft.Win32.Registry]::ClassesRoot.GetSubKeyNames()|Where-Object {$_ -match '^AutoCAD\.Application\.\d+(\.\d+)?$'})
$running=@(Get-CimInstance Win32_Process -Filter "Name='acad.exe'" -ErrorAction SilentlyContinue|Select-Object ProcessId,ExecutablePath)
[ordered]@{windows_x64=$windowsX64;driver_hash_matches=$hashOkay;driver_version=$version;python=$python;autocad_progids=$progIds;running_autocad=$running;prerequisites_ready=($windowsX64 -and $hashOkay -and [bool]$python);drawing_control_verified=$false;next='Discover exact windows and validate a disposable drawing before claiming compatibility.'}|ConvertTo-Json -Depth 5
if(-not($windowsX64 -and $hashOkay -and $python)){exit 2}
