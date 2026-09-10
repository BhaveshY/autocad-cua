import argparse,contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_sequence as runner

def state(prompt='idle',editor=True):
    tree='- Text "'+prompt+'"'
    if editor:tree+='\n- [4] Edit [id=local:AutoCompleteEdit_1 actions=[set_value,text]]'
    return {'structuredContent':{'tree_markdown':tree}}

class PromptTests(unittest.TestCase):
    def test_complete_shallow_prompt_uses_one_read(self):
        client=Mock();client.call.return_value=(state(),10)
        result,ms=runner.read_prompt(client,{'pid':1,'window_id':3},'^idle$')
        self.assertEqual(ms,10);self.assertEqual(client.call.call_count,1)
        self.assertEqual(client.call.call_args.args[1]['max_depth'],2)

    def test_matching_prefix_without_editor_requires_full_read(self):
        client=Mock();client.call.side_effect=[(state('idle',False),10),(state('different'),20)]
        result,ms=runner.read_prompt(client,{},'idle')
        self.assertEqual(runner.prompt_of(result)[0],'different');self.assertEqual(ms,30)
        self.assertEqual(client.call.call_args.args[1]['max_depth'],5)

    def test_unexpected_shallow_prompt_requires_full_read(self):
        client=Mock();client.call.side_effect=[(state('old'),10),(state('ready'),20)]
        result,ms=runner.read_prompt(client,{},'ready')
        self.assertEqual(runner.prompt_of(result)[0],'ready');self.assertEqual(client.call.call_count,2)

    def test_diagnostic_mode_preserves_original_scan(self):
        client=Mock();client.call.return_value=(state('custom',False),30)
        with self.assertRaisesRegex(RuntimeError, 'editor missing'):
            runner.read_prompt(client,{},'custom',full=True)
        self.assertEqual(client.call.call_count,1)
        self.assertEqual(client.call.call_args.args[1]['max_depth'],5)

    def test_shared_client_keeps_connection_and_all_checks(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(runner,'Client') as factory:
            root=Path(folder);path=root/'sequence.json'
            path.write_text(json.dumps({'initial_prompt':'idle','steps':[{'text':'one','after':'idle'},{'text':'two','after':'idle'}]}))
            options=argparse.Namespace(pid=1,window=2,command_window=3,expected_title='drawing',prompt_timeout=1,sequence=str(path),output=str(root/'one'))
            client=Mock();client.output=root
            def call(name,args):
                if name=='type_text':return {},1
                if args['window_id']==2:return {'structuredContent':{'window_title':'drawing'}},1
                return state(),1
            client.call.side_effect=call
            capture=io.StringIO()
            with contextlib.redirect_stdout(capture):
                a=runner.run(options,client=client)
                options.output=str(root/'two');b=runner.run(options,client=client)
            factory.assert_not_called();client.close.assert_not_called()
            self.assertTrue(a['client_reused'] and b['client_reused'])
            self.assertEqual(len(capture.getvalue().splitlines()),2)
            self.assertEqual(len(a['steps']),2)
            calls=client.call.call_args_list
            self.assertEqual(sum(c.args[0]=='type_text' for c in calls),4)
            self.assertEqual(sum(c.args[0]=='get_window_state' and c.args[1]['window_id']==2 for c in calls),4)
            self.assertEqual(sum(c.args[0]=='get_window_state' and c.args[1]['window_id']==3 for c in calls),8)
            self.assertEqual(json.loads((root/'two/summary.json').read_text())['steps'][1]['text'],'two')

    def test_unknown_or_unguarded_operations_never_reach_driver(self):
        client=runner.Client.__new__(runner.Client);client.rpc=Mock();client.background_fault=None
        for name in ['hotkey','activate_app','set_window_frame','clipboard_write','set_value','launch_app','invented_tool']:
            with self.subTest(name=name),self.assertRaises(ValueError):client.call(name,{})
        client.rpc.assert_not_called()

if __name__=='__main__':unittest.main()
