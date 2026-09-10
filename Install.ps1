param([string]$CodexPath,[switch]$CheckOnly)
$ErrorActionPreference='Stop'
$pluginRoot=$PSScriptRoot
$manifest=Get-Content -LiteralPath (Join-Path $pluginRoot '.codex-plugin\plugin.json') -Raw|ConvertFrom-Json
if($manifest.name -ne 'autocad-cua'){throw 'Unexpected plugin identity.'}
$runtime=Get-Content -LiteralPath (Join-Path $pluginRoot 'runtime.json') -Raw|ConvertFrom-Json
$stream=[IO.File]::OpenRead((Join-Path $pluginRoot 'bin\cua-driver.exe'))
$algorithm=[Security.Cryptography.SHA256]::Create()
try {$actualHash=[BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-','')}
finally {$stream.Dispose();$algorithm.Dispose()}
if($actualHash -ne $runtime.sha256){throw 'Driver integrity check failed.'}
if(-not $CodexPath){$CodexPath=(Get-Command codex -ErrorAction SilentlyContinue|Select-Object -First 1).Source}
if(-not $CodexPath){$CodexPath=Join-Path $env:LOCALAPPDATA 'Programs\OpenAI\Codex\bin\codex.exe'}
if(-not(Test-Path -LiteralPath $CodexPath)){throw 'Codex CLI was not found. Install/update the Codex app, then retry.'}
$version=(& $CodexPath --version 2>&1|Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $version -notmatch '^codex-cli '){throw 'Codex CLI version probe failed.'}
$destination=Join-Path $env:USERPROFILE 'plugins\autocad-cua'
$marketPath=Join-Path $env:USERPROFILE '.agents\plugins\marketplace.json'
$sameLocation=[IO.Path]::GetFullPath($pluginRoot).TrimEnd('\') -eq [IO.Path]::GetFullPath($destination).TrimEnd('\')
if((Test-Path -LiteralPath $destination) -and -not $sameLocation){throw "A plugin already exists at $destination. This installer will not overwrite it. Keep the current version or have Codex perform a reviewed update."}
if(Test-Path -LiteralPath $marketPath){$market=Get-Content -LiteralPath $marketPath -Raw|ConvertFrom-Json}
else{$market=[pscustomobject]@{name='personal';interface=[pscustomobject]@{displayName='Personal'};plugins=@()}}
if($market.name -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid personal marketplace name.'}
$pluginEntries=@($market.plugins|Where-Object name -eq 'autocad-cua')
if($pluginEntries.Count -gt 1 -or ($pluginEntries.Count -eq 1 -and ($pluginEntries[0].source.source -ne 'local' -or $pluginEntries[0].source.path -ne './plugins/autocad-cua'))){throw 'Conflicting marketplace entry; no changes made.'}
$doctor = (& (Join-Path $pluginRoot 'scripts\doctor.ps1') | Out-String) | ConvertFrom-Json
if(-not $doctor.prerequisites_ready){throw 'Windows x64, a valid bundled driver and Python 3.10+ are required. See README.md.'}
if($CheckOnly){[ordered]@{codex=$version;destination=$destination;marketplace=$market.name;driver_verified=$true;changes_made=$false}|ConvertTo-Json;exit 0}
if(-not $sameLocation){
 New-Item -ItemType Directory -Force (Split-Path $destination -Parent)|Out-Null
 New-Item -ItemType Directory -Path $destination | Out-Null
 Get-ChildItem -LiteralPath $pluginRoot -Force | Where-Object {$_.Name -notin @('.git','__pycache__','artifacts','evidence')} | Copy-Item -Destination $destination -Recurse
}
if($pluginEntries.Count -eq 0){
 $entry=[pscustomobject]@{name='autocad-cua';source=[pscustomobject]@{source='local';path='./plugins/autocad-cua'};policy=[pscustomobject]@{installation='AVAILABLE';authentication='ON_INSTALL'};category='Productivity'}
 $market.plugins=@($market.plugins)+@($entry)
 New-Item -ItemType Directory -Force (Split-Path $marketPath -Parent)|Out-Null
 if(Test-Path -LiteralPath $marketPath){Copy-Item -LiteralPath $marketPath -Destination ($marketPath+'.backup-'+[datetime]::UtcNow.ToString('yyyyMMddHHmmssfff'))}
 $temp=$marketPath+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
 $json=$market|ConvertTo-Json -Depth 30
 [IO.File]::WriteAllText($temp,$json,(New-Object Text.UTF8Encoding($false)))
 Move-Item -LiteralPath $temp -Destination $marketPath -Force
}
& $CodexPath plugin add ('autocad-cua@'+$market.name)
if($LASTEXITCODE -ne 0){throw 'Codex did not confirm installation. The local source and marketplace entry remain available for diagnosis.'}
Write-Host 'Installed AutoCAD Cua. Start a new Codex thread and ask it to check AutoCAD Cua setup.'
