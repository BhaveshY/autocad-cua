param(
 [Parameter(Mandatory=$true)][long]$ExpectedWindow,
 [Parameter(Mandatory=$true)][string]$ExpectedPath,
 [Parameter(Mandatory=$true)][string]$OutputPath,
 [Parameter(Mandatory=$true)][string]$ProgId,
 [switch]$IdentityOnly,
 [switch]$Detailed,
 [string]$Handles,
 [ValidateRange(1,10000)][int]$MaxEntities=100
)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputPath){throw 'Use a new output file; evidence is not overwritten.'}
function Read-Property($Object,[string]$Name) {
 Set-StrictMode -Version 2
 return ,($Object.$Name)
}
function Read-Method($Object,[string]$Name,[object[]]$Arguments) {
 try { return ,($Object.GetType().InvokeMember($Name,[Reflection.BindingFlags]::InvokeMethod,$null,$Object,$Arguments)) }
 catch { throw "AutoCAD read method $Name failed: $($_.Exception.Message)" }
}
$app=[Runtime.InteropServices.Marshal]::GetActiveObject($ProgId)
$window=[long](Read-Property $app HWND)
$document=Read-Property $app ActiveDocument
$path=[string](Read-Property $document FullName)
if($window -ne $ExpectedWindow -or $path -ne $ExpectedPath){throw 'Exact drawing binding changed.'}
$space=Read-Property $document ModelSpace
$count=[int](Read-Property $space Count)
$entities=@()
$selectedHandles=@($Handles -split ','|Where-Object {$_})
$readCount=if($IdentityOnly){0}elseif($selectedHandles.Count){[Math]::Min($selectedHandles.Count,$MaxEntities)}else{[Math]::Min($count,$MaxEntities)}
for($i=0;$i -lt $readCount;$i++) {
 $entity=if($selectedHandles.Count){Read-Method $document HandleToObject @([string]$selectedHandles[$i])}else{Read-Method $space Item @($i)}
 $item=[ordered]@{handle=Read-Property $entity Handle;type=Read-Property $entity ObjectName}
 $item.geometry_supported=$item.type -in @('AcDbLine','AcDbPolyline','AcDbArc','AcDbCircle','AcDbText','AcDbMText') -or $item.type -like '*Dimension'
 if($item.type -eq 'AcDbLine'){$item.start=Read-Property $entity StartPoint;$item.end=Read-Property $entity EndPoint}
 if($item.type -eq 'AcDbPolyline'){$item.coordinates=Read-Property $entity Coordinates;$item.closed=Read-Property $entity Closed;$item.area=Read-Property $entity Area}
 if($item.type -eq 'AcDbArc'){$item.center=Read-Property $entity Center;$item.radius=Read-Property $entity Radius;$item.start_angle=Read-Property $entity StartAngle;$item.end_angle=Read-Property $entity EndAngle}
 if($item.type -eq 'AcDbCircle'){$item.center=Read-Property $entity Center;$item.radius=Read-Property $entity Radius}
 if($item.type -in @('AcDbText','AcDbMText')){$item.text=Read-Property $entity TextString;$item.insertion=Read-Property $entity InsertionPoint}
 if($item.type -like '*Dimension'){$item.measurement=Read-Property $entity Measurement;$item.text_override=Read-Property $entity TextOverride}
 $item.layer=Read-Property $entity Layer
 if($Detailed){
  $minimum=$null;$maximum=$null
  $entity.GetBoundingBox([ref]$minimum,[ref]$maximum)
  $item.bounds_min=$minimum;$item.bounds_max=$maximum
  if($item.type -in @('AcDbText','AcDbMText')){
   $item.text_height=Read-Property $entity Height
   $item.rotation=Read-Property $entity Rotation
   $item.style_name=Read-Property $entity StyleName
  }
  if($item.type -like '*Dimension'){
   $item.text_position=Read-Property $entity TextPosition
   $item.text_height=Read-Property $entity TextHeight
   $item.scale_factor=Read-Property $entity ScaleFactor
   $item.style_name=Read-Property $entity StyleName
  }
 }
 $entities+=$item
}
$state=[ordered]@{utc=[datetime]::UtcNow.ToString('o');window=$window;path=$path;saved=Read-Property $document Saved;model_space_count=$count;cmdactive=Read-Method $document GetVariable @('CMDACTIVE');cmdnames=Read-Method $document GetVariable @('CMDNAMES');entities=$entities}
$state.returned_entity_count=$entities.Count
$state.scope=if($IdentityOnly){'identity_only'}elseif($selectedHandles.Count){'requested_handles'}else{'model_space'}
$state.complete=if($IdentityOnly){$false}elseif($selectedHandles.Count){$readCount -eq $selectedHandles.Count}else{$readCount -eq $count}
$state.variables=[ordered]@{}
foreach($name in @('INSUNITS','TILEMODE','CVPORT','CTAB','OSMODE','ORTHOMODE','SNAPMODE','UCSORG','UCSXDIR','UCSYDIR','CLAYER','DIMSCALE')) {
 $state.variables[$name]=Read-Method $document GetVariable @($name)
}
if((Read-Property $app HWND) -ne $ExpectedWindow -or (Read-Property (Read-Property $app ActiveDocument) FullName) -ne $ExpectedPath){throw 'Drawing changed during verification; no acceptance output written.'}
$state|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 $OutputPath
