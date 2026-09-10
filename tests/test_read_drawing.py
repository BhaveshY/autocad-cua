import base64,json,os,subprocess,unittest
from pathlib import Path

@unittest.skipUnless(os.name=='nt','Windows PowerShell reader')
class ReadDrawingTests(unittest.TestCase):
    def test_property_values_preserved_and_missing_property_fails(self):
        path=str(Path(__file__).resolve().parents[1]/'scripts/read_drawing.ps1').replace("'","''")
        code=r"""
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PATH',[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Invalid PowerShell script'}
$node=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Read-Property'},$true)
. ([scriptblock]::Create($node.Extent.Text))
$o=[pscustomobject]@{zero=0;empty='';flag=$false;array=@(1,2);nullable=$null}
$result=[ordered]@{}
foreach($name in @('zero','empty','flag','array','nullable')){$result[$name]=Read-Property $o $name}
$missing=$false
try {Read-Property $o absent}catch{$missing=$true}
$result.missing_failed=$missing
$result|ConvertTo-Json -Compress
""".replace('PATH',path)
        ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        r=subprocess.run([str(ps),'-NoProfile','-EncodedCommand',base64.b64encode(code.encode('utf-16-le')).decode()],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout),dict(zero=0,empty='',flag=False,array=[1,2],nullable=None,missing_failed=True))

@unittest.skipUnless(os.name=='nt','Windows PowerShell reader')
class DrawingBindingTests(unittest.TestCase):
    def test_same_path_reopened_document_is_rejected(self):
        path=str(Path(__file__).resolve().parents[1]/'scripts/read_drawing.ps1').replace("'","''")
        code=r"""
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PATH',[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Invalid PowerShell script'}
foreach($name in @('Read-Property','Assert-DrawingBinding')){
 $node=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)
 . ([scriptblock]::Create($node.Extent.Text))
}
$app=[pscustomobject]@{HWND=2;ActiveDocument=[pscustomobject]@{HWND=3;FullName='C:\fixture.dwg'}}
Assert-DrawingBinding $app 2 'C:\fixture.dwg' 3
$app.ActiveDocument.HWND=4
$rejected=$false
try{Assert-DrawingBinding $app 2 'C:\fixture.dwg' 3}catch{$rejected=$true}
if(-not $rejected){throw 'Reopened drawing accepted'}
$entities=[Collections.Generic.List[object]]::new()
$entities.Add([ordered]@{handle='A'})
@{reopened_rejected=$rejected;entities=$entities}|ConvertTo-Json -Compress
""".replace('PATH',path)
        ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        r=subprocess.run([str(ps),'-NoProfile','-EncodedCommand',base64.b64encode(code.encode('utf-16-le')).decode()],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout),dict(reopened_rejected=True,entities=[dict(handle='A')]))


if __name__=='__main__':unittest.main()
