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
 if($request.target){foreach($key in @('pid','window','document_window','process_started','path','file_sha256')){if([string]$target[$key] -cne [string]$request.target.$key){throw "Drawing binding changed: $key"}}}
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
 } elseif($request.operation -eq 'inspect'){
  if($request.max_entities -or $request.handles){
   $geometry=$OutputPath+'.geometry.json'
   $params=@{ExpectedWindow=$target.window;ExpectedPath=$target.path;ProgId=$target.prog_id;OutputPath=$geometry;MaxEntities=[int]$request.max_entities}
   if($request.handles){$params.Handles=(@($request.handles)-join ',')}
   & (Join-Path $PSScriptRoot 'read_drawing.ps1') @params
   $state.geometry=Get-Content -LiteralPath $geometry -Raw -Encoding UTF8|ConvertFrom-Json
  }
 }else{throw 'Unknown native operation'}
 @{ok=$true;state=$state}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $OutputPath -Encoding UTF8
}catch{
 @{ok=$false;error=$_.Exception.Message}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $OutputPath -Encoding UTF8
 exit 1
}
