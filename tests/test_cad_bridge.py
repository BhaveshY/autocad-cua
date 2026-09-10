import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cad_bridge import CadBridge,validate_code
from mcp_server import Server

TARGET=dict(prog_id='AutoCAD.Application.23',pid=1,window=2,document_window=3,process_started='test',path='C:\\fixture.dwg',file_sha256='a'*64)
class NativeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.b=CadBridge(self.temp.name)
  self.lease=patch('cad_bridge.DesktopLease').start();self.watch=patch('cad_bridge.BackgroundWatch').start()
  self.addCleanup(patch.stopall);self.watch.return_value.start.return_value.finish.return_value=None
  self.state=dict(target=TARGET,cmdactive=0,cmdnames='',model_space_count=0)
  def host(request,folder,timeout=20):
   if request['operation']=='execute':(folder/'completion.txt').write_text('ok\n42\n')
   return self.state
  self.b.host=Mock(side_effect=host)
 def job(self,**kw):return self.b.prepare(TARGET,'(+ 2 3)','T','test',**kw)
 def test_prepare_does_not_touch_app(self):
  j=self.job();self.b.host.assert_not_called();self.assertEqual(self.b.result(j['job'])['status'],'prepared')
 def test_changed_code_hash_never_dispatches(self):
  j=self.job();p=self.b.folder(j['job'])/'plan.json';d=json.loads(p.read_text());d['code']='(exit)';p.write_text(json.dumps(d))
  with self.assertRaisesRegex(ValueError,'hash mismatch'):self.b.execute(j['job'],j['sha256'])
  self.b.host.assert_not_called()
 def test_duplicate_call_is_idempotent(self):
  j=self.job();self.assertEqual(self.b.execute(j['job'],j['sha256'])['status'],'executed');count=self.b.host.call_count
  self.assertEqual(self.b.execute(j['job'],j['sha256'])['status'],'executed');self.assertEqual(self.b.host.call_count,count)
 def test_stale_target_preflight_never_writes_execution(self):
  j=self.job();self.b.host.side_effect=RuntimeError('target changed')
  with self.assertRaises(RuntimeError):self.b.execute(j['job'],j['sha256'])
  self.assertFalse((self.b.folder(j['job'])/'execution.json').exists())
 def test_busy_command_never_dispatches(self):
  j=self.job();self.state['cmdactive']=1
  with self.assertRaisesRegex(RuntimeError,'active command'):self.b.execute(j['job'],j['sha256'])
  self.assertEqual(self.b.host.call_count,1)
 def test_uncertain_outcome_blocks_new_job_and_never_replays(self):
  j=self.job();self.b.host.side_effect=[self.state,TimeoutError('late')]
  self.assertEqual(self.b.execute(j['job'],j['sha256'])['status'],'uncertain')
  self.assertEqual(self.b.execute(j['job'],j['sha256'])['status'],'uncertain');self.assertEqual(self.b.host.call_count,2)
  other=self.job()
  with self.assertRaisesRegex(RuntimeError,'previous native job'):self.b.execute(other['job'],other['sha256'])
 def test_resolution_requires_idle_and_does_not_claim_success(self):
  j=self.job();folder=self.b.folder(j['job']);(folder/'execution.json').write_text('{"status":"uncertain"}')
  self.state['cmdactive']=1
  with self.assertRaisesRegex(RuntimeError,'busy'):self.b.result(j['job'],True)
  self.state['cmdactive']=0;r=self.b.result(j['job'],True)
  self.assertEqual(r['status'],'uncertain');self.assertTrue(r['resolved_after_inspection']);self.assertFalse(r['geometry_verified'])
 def test_late_completion_can_be_read_without_replay(self):
  j=self.job();folder=self.b.folder(j['job']);(folder/'execution.json').write_text('{"status":"uncertain"}')
  (folder/'completion.txt').write_text('error\npartial\n');self.assertEqual(self.b.result(j['job'])['status'],'failed');self.b.host.assert_not_called()
 def test_job_path_escape_is_rejected(self):
  for value in ['../file','A'*32,'','0'*31]:
   with self.assertRaises(ValueError):self.b.result(value)
 def test_code_balance_ignores_strings_and_comments(self):
  validate_code('(list "()\\\"" ; unmatched ) comment\n 1)')
  for code in ['','(x','x)','"unterminated']:
   with self.assertRaises(ValueError):validate_code(code)
 def test_long_source_roundtrips_in_short_chunks(self):
  j=self.b.prepare(TARGET,'\n'.join('(setq x "quoted \\\"value\\\"")' for _ in range(300)),'T','large')
  plan=j['plan'];marker=Path(self.temp.name)/'done.txt';commands=self.b.commands(plan,marker,j['job'])
  self.assertTrue(all(len(c)<1024 for c in commands))
  # Recover each quoted staging payload using JSON-compatible Lisp escapes.
  chunks=[]
  for c in commands[1:-2]:
   start=c.index(' "')+1;end=c.rindex(')) (princ))')
   chunks.append(json.loads(c[start:end]))
  self.assertEqual(''.join(chunks),self.b.command(plan,marker))
 def test_mcp_native_execution_cannot_overlap_cua_session(self):
  server=Server();server.client=Mock()
  with self.assertRaisesRegex(RuntimeError,'End the Cua session'):server.call('cad_execute',{'job':'a'*32,'sha256':'b'*64})
 def test_opt_in_validation_is_strict(self):
  j=self.job()
  with self.assertRaises(ValueError):self.b.execute(j['job'],j['sha256'],'true')
  with self.assertRaises(ValueError):self.job(undo_group='false')
 def test_inspection_bounds_are_validated(self):
  with self.assertRaises(ValueError):self.b.inspect(max_entities=10001)
  with self.assertRaises(ValueError):self.b.inspect(handles=['not-a-handle'])
  self.b.host.assert_not_called()

 def test_partial_or_invalid_receipt_keeps_next_job_blocked(self):
  for content in ('', 'ok', 'ok\n', 'ok\nunfinished', 'unknown\nvalue\n'):
   with self.subTest(content=content):
    j=self.job();folder=self.b.folder(j['job'])
    (folder/'execution.json').write_text('{"status":"uncertain"}')
    (folder/'completion.txt').write_text(content)
    self.assertEqual(self.b.result(j['job'])['status'],'uncertain')
    other=self.job()
    with self.assertRaisesRegex(RuntimeError,'previous native job'):
     self.b.execute(other['job'],other['sha256'])
    self.b.host.assert_not_called()
    (folder/'completion.txt').write_text('error\nresolved test fixture\n')

 def test_partial_receipt_can_be_resolved_only_after_idle_inspection(self):
  j=self.job();folder=self.b.folder(j['job'])
  (folder/'execution.json').write_text('{"status":"uncertain"}')
  (folder/'completion.txt').write_text('ok\n')
  self.state['cmdactive']=1
  with self.assertRaisesRegex(RuntimeError,'busy'):self.b.result(j['job'],True)
  self.state['cmdactive']=0
  answer=self.b.result(j['job'],True)
  self.assertEqual(answer['status'],'uncertain')
  self.assertTrue(answer['resolved_after_inspection'])

 def test_unreadable_receipt_remains_uncertain(self):
  from cad_bridge import completion
  with patch.object(Path,'read_text',side_effect=PermissionError('writer owns file')):
   self.assertIsNone(completion(Path(self.temp.name)))

 def test_generated_receipt_is_closed_before_publication(self):
  j=self.job();source=self.b.command(j['plan'],Path(self.temp.name)/'completion.txt')
  validate_code(source)
  self.assertIn('completion.txt.tmp',source)
  self.assertLess(source.index('(close cb-file)'),source.index('(vl-file-rename'))


if __name__=='__main__':unittest.main()
