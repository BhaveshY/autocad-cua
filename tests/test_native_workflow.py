import json,copy
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cad_bridge import CadBridge,validate_code
from mcp_server import Server
TARGET=dict(prog_id='AutoCAD.Application.23',pid=1,window=2,document_window=3,process_started='same',path='C:\\one.dwg',file_sha256='a'*64)

class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.b=CadBridge(self.temp.name);self.state=dict(target=dict(TARGET),cmdactive=0,cmdnames='',model_space_count=3)
  self.b.host=Mock(side_effect=lambda *a,**k:copy.deepcopy(self.state))
 def test_active_document_switch_never_rebinds_inspect_or_prepare(self):
  first=self.b.inspect();self.state['target']=dict(TARGET,path='C:\\two.dwg',document_window=4)
  with self.assertRaisesRegex(RuntimeError,'Task drawing changed'):self.b.inspect(max_entities=10)
  with self.assertRaisesRegex(RuntimeError,'Task drawing changed'):self.b.prepare(self.state['target'],'T','T','wrong')
  self.assertEqual(self.b.bound,TARGET)
  self.assertFalse(list(Path(self.temp.name).glob('*/plan.json')))
 def test_resuming_across_processes_retains_original_target(self):
  first=self.b.inspect();resumed=CadBridge(self.temp.name,task=first['task']);resumed.host=self.b.host
  self.state['target']=dict(TARGET,document_window=5)
  with self.assertRaisesRegex(RuntimeError,'Task drawing changed'):resumed.inspect()
 def test_saved_hash_refresh_does_not_reset_document_identity(self):
  first=self.b.inspect();self.state['target']=dict(TARGET,file_sha256='b'*64)
  after=self.b.inspect();self.assertEqual(first['task'],after['task']);self.assertEqual(after['target']['file_sha256'],'b'*64)
  self.assertTrue(self.b.host.call_args.args[0]['refresh_file_hash'])
 def test_explicit_new_task_is_required_for_different_drawing(self):
  first=self.b.inspect();self.state['target']=dict(TARGET,path='C:\\two.dwg',document_window=5)
  second=self.b.inspect(new_task=True);self.assertNotEqual(first['task'],second['task'])
 def test_mcp_preserves_bridge_between_calls(self):
  server=Server();server.cad=self.b;server.call('cad_inspect',{})
  self.state['target']=dict(TARGET,path='C:\\two.dwg')
  with self.assertRaisesRegex(RuntimeError,'Task drawing changed'):server.call('cad_inspect',{})
 def test_replacement_requires_new_backup_and_helpers(self):
  for kwargs in ({'replace_model':True},{'replace_model':True,'helpers':True,'backup_path':'relative.dwg'}):
   with self.assertRaises(ValueError):self.b.prepare(TARGET,'T','T','replace',**kwargs)
  backup=Path(self.temp.name)/'existing.dwg';backup.write_bytes(b'old')
  with self.assertRaises(ValueError):self.b.prepare(TARGET,'T','T','replace',helpers=True,replace_model=True,backup_path=str(backup))
  self.b.host.assert_not_called()
 def test_prerequisites_precede_deletion_and_helpers_are_frozen(self):
  j=self.b.prepare(TARGET,'(acua:finish)','T','replace',helpers=True,replace_model=True,backup_path=str(Path(self.temp.name)/'backup.dwg'),setup_code='(acua:layer "TEST" 7 25)')
  src=self.b.command(j['plan'],Path(self.temp.name)/'completion.txt');validate_code(src)
  self.assertLess(src.rindex('(acua:init)'),src.rindex('(acua:clear-model)'))
  self.assertLess(src.index('(acua:layer "TEST"'),src.rindex('(acua:clear-model)'))
  self.assertIn('Cua-Text',j['plan']['helper_source'])
 def test_backup_failure_never_dispatches_code_or_wedges_next_job(self):
  j=self.b.prepare(TARGET,'T','T','replace',helpers=True,replace_model=True,backup_path=str(Path(self.temp.name)/'backup.dwg'))
  self.b.host.side_effect=[self.state,RuntimeError('backup failed')]
  with patch('cad_bridge.DesktopLease'),patch('cad_bridge.BackgroundWatch') as w:
   w.return_value.start.return_value.finish.return_value=None
   result=self.b.execute(j['job'],j['sha256'])
  self.assertEqual(result['status'],'failed');self.assertFalse(result['code_dispatch_attempted'])
  self.assertEqual([c.args[0]['operation'] for c in self.b.host.call_args_list],['inspect','backup'])
 def test_targeted_readback_does_not_request_full_geometry(self):
  self.b.inspect(handles=['ABC'],detailed=True)
  req=self.b.host.call_args.args[0];self.assertEqual(req['max_entities'],1);self.assertEqual(req['handles'],['ABC']);self.assertTrue(req['detailed'])

if __name__=='__main__':unittest.main()
