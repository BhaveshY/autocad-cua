import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import cua
import run_sequence as runner
import runtime

class Guards(unittest.TestCase):
    def test_invoke_requires_current_exact_id_and_invoke_pattern(self):
        selector=dict(label='Rectangle',role='Button',automation_id='RECT_EXECUTE')
        element=dict(label='Rectangle',role='Button',enabled=True,actions=['invoke'],element_index=7,element_token='s00000002:7')
        state={'structuredContent':{'tree_markdown':'- [7] Button "Rectangle" [id=RECT_EXECUTE actions=[invoke]]','elements':[element]}}
        self.assertEqual(cua.invocation_match(state,selector),'s00000002:7')
        for change in [dict(automation_id='WRONG'),dict(label='Circle')]:
            with self.assertRaises(RuntimeError):cua.invocation_match(state,dict(selector,**change))
        element['actions']=['toggle']
        with self.assertRaises(RuntimeError):cua.invocation_match(state,selector)

    def options(self, root, spec):
        path = root / 'sequence.json'
        path.write_text(json.dumps(spec), encoding='utf-8')
        return argparse.Namespace(pid=1,window=2,command_window=3,expected_title='AutoCAD [test.dwg]',
            prompt_timeout=.001,sequence=str(path),output=str(root/'evidence'),full_prompts=True)

    def test_invalid_sequence_never_launches_driver(self):
        cases = [dict(initial_prompt='idle',steps=[]),dict(steps=[dict(text='_U',after='idle')]),
            dict(initial_prompt='[',steps=[dict(text='_U',after='idle')]),
            dict(initial_prompt='idle',steps=[dict(text='_U\n_QSAVE',after='idle')]),
            dict(initial_prompt='idle',steps=[dict(text='_U',after='')])]
        for spec in cases:
            with self.subTest(spec=spec), tempfile.TemporaryDirectory() as temp:
                with patch.object(runner,'Client') as client:
                    with self.assertRaises((ValueError,KeyError,runner.re.error)):
                        runner.run(self.options(Path(temp),spec))
                    client.assert_not_called()

    def test_title_is_exact_except_modified_marker_and_case(self):
        self.assertEqual(runner.title_key('AutoCAD [test.dwg*]'),runner.title_key('AUTOCAD [TEST.DWG]'))
        self.assertNotEqual(runner.title_key('test.dwg'),runner.title_key('copy-test.dwg'))

    def test_wrong_title_sends_no_input(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runner,'Client') as factory:
            options=self.options(Path(temp),dict(initial_prompt='idle',steps=[dict(text='_U',after='idle')]))
            client=factory.return_value
            client.call.side_effect=[({'structuredContent':{'tree_markdown':'- Text "idle"\n- [1] Edit [id=local:AutoCompleteEdit_1]'}},1),
                                     ({'structuredContent':{'window_title':'AutoCAD [copy-test.dwg]'}},1)]
            with self.assertRaisesRegex(RuntimeError,'Drawing title changed'):
                runner.run(options)
            self.assertFalse(any(c.args[0]=='type_text' for c in client.call.call_args_list))

    def test_prompt_timeout_never_replays(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runner,'Client') as factory:
            options=self.options(Path(temp),dict(initial_prompt='idle',steps=[dict(text='_U',after='changed')]))
            client=factory.return_value
            def call(name,args):
                if name=='type_text':
                    self.assertEqual(args['delivery_mode'],'background')
                    return {},1
                if args['window_id']==2:
                    return {'structuredContent':{'window_title':options.expected_title}},1
                return {'structuredContent':{'tree_markdown':'- Text "idle"\n- [1] Edit [id=local:AutoCompleteEdit_1]'}},1
            client.call.side_effect=call
            with self.assertRaisesRegex(RuntimeError,'not replayed'):
                runner.run(options)
            self.assertEqual(sum(c.args[0]=='type_text' for c in client.call.call_args_list),1)

    def test_foreground_desktop_overrides_and_stale_tokens_rejected(self):
        good=dict(pid=1,window_id=2,delivery_mode='background')
        cua.check_call('type_text',good)
        for change in [dict(delivery_mode='foreground'),dict(pid=0),dict(scope='desktop'),
                       dict(target={'kind':'desktop','display_id':'primary'}),dict(element_token='s00000001:1')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                cua.check_call('click',dict(good,**change))
        with self.assertRaises(ValueError):
            cua.check_call('activate_app',good)

    def test_hash_mismatch_prevents_driver_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'bin').mkdir();(root/'bin'/'cua-driver.exe').write_bytes(b'changed')
            (root/'runtime.json').write_text(json.dumps(dict(sha256='0'*64)))
            with patch.object(runtime,'ROOT',root), self.assertRaisesRegex(RuntimeError,'hash mismatch'):
                runtime.driver_path()

    def test_non_latin_prompt_and_console(self):
        self.assertEqual(runner.prompt_of({'structuredContent':{'tree_markdown':'- Text "下一点"\n- [0] Edit "输入"'}})[0],'下一点')
        with tempfile.TemporaryDirectory() as temp, patch.object(runner,'Client') as factory:
            options=self.options(Path(temp),dict(initial_prompt='下一点',steps=[dict(text='0,0',after='下一点')]))
            client=factory.return_value
            def call(name,args):
                if name=='type_text':return {},1
                if args['window_id']==2:return {'structuredContent':{'window_title':options.expected_title}},1
                return {'structuredContent':{'tree_markdown':'- Text "下一点"\n- [1] Edit [id=local:AutoCompleteEdit_1]'}},1
            client.call.side_effect=call
            stream=io.TextIOWrapper(io.BytesIO(),encoding='cp1252')
            with contextlib.redirect_stdout(stream):runner.run(options)
            stream.flush()
            self.assertEqual(json.loads((Path(options.output)/'summary.json').read_text(encoding='utf-8'))['status'],'prompts_verified')

if __name__=='__main__':
    unittest.main()
