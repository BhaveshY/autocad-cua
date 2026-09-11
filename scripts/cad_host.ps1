param([Parameter(Mandatory=$true)][string]$RequestPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$request=Get-Content -LiteralPath $RequestPath -Raw -Encoding UTF8|ConvertFrom-Json
function Prop($o,[string]$n){Set-StrictMode -Version 2;return ,($o.$n)}
function Call($o,[string]$n,[object[]]$methodArgs){try{return ,($o.GetType().InvokeMember($n,[Reflection.BindingFlags]::InvokeMethod,$null,$o,$methodArgs))}catch{throw "Native $n ($methodArgs) failed: $($_.Exception.Message)"}}
Add-Type 'using System;using System.Runtime.InteropServices;public static class CadBridgeOwner{[DllImport("user32.dll")]public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);}'
try {
 $ids=if($request.target){@($request.target.prog_id)}else{@([Microsoft.Win32.Registry]::ClassesRoot.GetSubKeyNames()|Where-Object {$_ -match '^AutoCAD\.Application\.\d+(\.\d+)?$'})}
 $found=@{}
 foreach($id in $ids){
  try {
   $candidate=[Runtime.InteropServices.Marshal]::GetActiveObject($id)
   $h=[long](Prop $candidate HWND);[uint32]$owner=0
   [void][CadBridgeOwner]::GetWindowThreadProcessId([IntPtr]$h,[ref]$owner)
   if($owner -and (-not $request.pid -or $request.pid -eq $owner)){$found[$h]=@{app=$candidate;prog=$id;pid=$owner}}
  } catch {}
 }
 if($found.Count -ne 1){throw 'Need exactly one running AutoCAD instance; specify its PID. No application was launched.'}
 $entry=@($found.Values)[0];$app=$entry.app;$doc=Prop $app ActiveDocument
 $path=[string](Prop $doc FullName)
 $diskHash=$null
 if([IO.Path]::IsPathRooted($path) -and [IO.File]::Exists($path)){
  $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite);$hash=[Security.Cryptography.SHA256]::Create()
  try{$diskHash=[BitConverter]::ToString($hash.ComputeHash($stream)).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose();$stream.Dispose()}
 }
 $target=[ordered]@{prog_id=$entry.prog;pid=$entry.pid;window=[long](Prop $app HWND);document_window=[long](Prop $doc HWND);process_started=(Get-Process -Id $entry.pid).StartTime.ToUniversalTime().ToString('o');path=$path;file_sha256=$diskHash}
 if($request.target){foreach($key in @('pid','window','document_window','process_started','path','file_sha256')){if($key -eq 'file_sha256' -and $request.operation -eq 'inspect' -and $request.refresh_file_hash){continue};if([string]$target[$key] -cne [string]$request.target.$key){throw "Drawing binding changed: $key"}}}
 $state=[ordered]@{target=$target;cmdactive=[int](Call $doc GetVariable @('CMDACTIVE'));cmdnames=[string](Call $doc GetVariable @('CMDNAMES'));model_space_count=[int](Prop (Prop $doc ModelSpace) Count);saved=[bool](Prop $doc Saved);units=Call $doc GetVariable @('INSUNITS');space=Call $doc GetVariable @('CTAB');ucs_origin=Call $doc GetVariable @('UCSORG');ucs_x=Call $doc GetVariable @('UCSXDIR');ucs_y=Call $doc GetVariable @('UCSYDIR')}
 if($request.operation -eq 'execute'){
  if($state.cmdactive -ne 0 -or $state.cmdnames){throw 'AutoCAD is busy; inspect its command state before preparing another execution.'}
  if(-not [IO.Path]::IsPathRooted($target.path) -or -not (Test-Path -LiteralPath $target.path)){throw 'Save the intended drawing before native execution.'}
  if([string](Prop (Prop $app ActiveDocument) FullName) -cne $target.path){throw 'Active drawing changed before dispatch'}
  # The supplied command includes a second in-process identity/precondition check.
  foreach($command in $request.commands){
   if([long](Prop (Prop $app ActiveDocument) HWND) -ne $target.document_window){throw 'Active document changed during staging'}
   [void](Call $doc SendCommand @([string]$command))
  }
  $state.dispatch_returned=$true
 } elseif($request.operation -eq 'backup'){
  if($state.cmdactive -ne 0 -or $state.cmdnames){throw 'AutoCAD is busy; backup not started.'}
  $backupPath=[IO.Path]::GetFullPath([string]$request.backup_path)
  if($backupPath -eq $path -or [IO.File]::Exists($backupPath)){throw 'Backup must be a new file.'}
  [void](Call $doc Save @())
  if([long](Prop (Prop $app ActiveDocument) HWND) -ne $target.document_window){throw 'Drawing changed during backup.'}
  [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($backupPath))|Out-Null
  $inputFile=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
  try {
   $outputFile=[IO.File]::Open($backupPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
   try{$inputFile.CopyTo($outputFile)}finally{$outputFile.Dispose()}
   $inputFile.Position=0;$hash=[Security.Cryptography.SHA256]::Create()
   try{$sourceHash=[BitConverter]::ToString($hash.ComputeHash($inputFile)).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
  }finally{$inputFile.Dispose()}
  $backupStream=[IO.File]::OpenRead($backupPath);$hash=[Security.Cryptography.SHA256]::Create()
  try{$backupHash=[BitConverter]::ToString($hash.ComputeHash($backupStream)).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose();$backupStream.Dispose()}
  if($backupHash -cne $sourceHash){throw 'Backup hash mismatch; no drawing edits dispatched.'}
  $state.target.file_sha256=$sourceHash
  $state.backup=@{path=$backupPath;sha256=$backupHash;verified=$true}
 } elseif($request.operation -eq 'inspect'){
  if($request.max_entities -or $request.handles){
   $geometry=$OutputPath+'.geometry.json'
   $params=@{ExpectedWindow=$target.window;ExpectedDocumentWindow=$target.document_window;ExpectedPath=$target.path;ProgId=$target.prog_id;OutputPath=$geometry;MaxEntities=[int]$request.max_entities}
   if($request.handles){$params.Handles=(@($request.handles)-join ',')}
   if($request.detailed){$params.Detailed=$true}
   & (Join-Path $PSScriptRoot 'read_drawing.ps1') @params
   $state.geometry=Get-Content -LiteralPath $geometry -Raw -Encoding UTF8|ConvertFrom-Json
  }
 }else{throw 'Unknown native operation'}
 if([long](Prop $app HWND) -ne $target.window -or
    [long](Prop (Prop $app ActiveDocument) HWND) -ne $target.document_window -or
    [string](Prop (Prop $app ActiveDocument) FullName) -cne $target.path){throw 'Active drawing changed before receipt'}
 @{ok=$true;state=$state}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $OutputPath -Encoding UTF8
}catch{
 @{ok=$false;error=$_.Exception.Message}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $OutputPath -Encoding UTF8
 exit 1
}
