"""Failure injection: uncertain actions must not permit subsequent writes."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_sequence as runner


def snapshot(prompt='idle', editor=True):
    return {'structuredContent': {'tree_markdown': '- Text "' + prompt + '"' + (
        '\n- [1] Edit [id=local:AutoCompleteEdit_1]' if editor else '')}}


class FailureTests(unittest.TestCase):
    def test_preflight_refusal_sends_no_rpc_and_is_not_uncertain(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.BackgroundWatch') as factory:
            watch = factory.return_value.start.return_value
            watch.finish.return_value = None
            watch.check_target.side_effect = RuntimeError('foreground use')
            client = runner.Client.__new__(runner.Client)
            client.output = Path(folder); client.serial = 5; client.session = 'test'
            client.background_fault = None; client.input_fault = None; client.rpc = Mock()
            with self.assertRaisesRegex(RuntimeError, 'foreground use'):
                client.call('type_text', dict(pid=1, window_id=2, delivery_mode='background', text='x'))
            client.rpc.assert_not_called()
            self.assertFalse(json.loads(next(Path(folder).glob('*error.json')).read_text())['input_uncertain'])

    def test_failed_or_uncertain_input_blocks_write_but_allows_read(self):
        failures = [TimeoutError('timeout'), EOFError('exit'), ValueError('malformed JSON'),
                    {'isError': True}, {'structuredContent': {'code': 'background_unavailable'}},
                    {'structuredContent': {'status': 'refused'}}]
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder, patch('run_sequence.BackgroundWatch') as watch:
                watch.return_value.start.return_value.finish.return_value = None
                client = runner.Client.__new__(runner.Client)
                client.output = Path(folder); client.serial = 5; client.session = 'test'
                client.background_fault = None; client.input_fault = None
                client.rpc = Mock(side_effect=failure) if isinstance(failure, Exception) else Mock(return_value=failure)
                args = dict(pid=1, window_id=2, delivery_mode='background', text='x')
                with self.assertRaises(Exception): client.call('type_text', args)
                self.assertTrue(list(Path(folder).glob('*.json')))
                client.rpc.reset_mock(); client.rpc.side_effect = None; client.rpc.return_value = snapshot()
                with self.assertRaisesRegex(RuntimeError, 'further input blocked'): client.call('type_text', args)
                client.rpc.assert_not_called()
                client.call('get_window_state', dict(pid=1, window_id=2))
                client.rpc.assert_called_once()

    def test_missing_editor_never_qualifies_even_when_text_matches(self):
        for full in [False, True]:
            client = Mock(); client.call.return_value = (snapshot(editor=False), 1)
            with self.assertRaisesRegex(RuntimeError, 'editor missing'):
                runner.read_prompt(client, {}, '^idle$', full)

    def test_prompt_changes_between_steps_blocks_next_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); spec = root / 'sequence.json'
            spec.write_text(json.dumps(dict(initial_prompt='^idle$', steps=[
                dict(text='command', after='^next$'), dict(text='coordinate', after='^idle$')])) )
            options = argparse.Namespace(pid=1, window=2, command_window=3, expected_title='drawing',
                prompt_timeout=1, sequence=str(spec), output=str(root / 'run'))
            client = Mock(); client.output = root
            prompts = iter(['idle', 'next', 'unrelated', 'unrelated'])
            def call(name, args):
                if name == 'type_text': return {}, 1
                if args['window_id'] == 2: return {'structuredContent': {'window_title': 'drawing'}}, 1
                return snapshot(next(prompts)), 1
            client.call.side_effect = call
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, 'before step 2'):
                runner.run(options, client)
            self.assertEqual(sum(c.args[0] == 'type_text' for c in client.call.call_args_list), 1)
            self.assertTrue(client.input_fault)
            summary = json.loads((root / 'run/summary.json').read_text())
            self.assertEqual(summary['steps_completed'], 1)
            self.assertIn('before step 2', summary['error'])

    def test_boolean_window_target_never_reaches_driver(self):
        client = runner.Client.__new__(runner.Client)
        client.background_fault = None; client.rpc = Mock()
        for key in ['pid', 'window_id']:
            args = dict(pid=1, window_id=2, delivery_mode='background'); args[key] = True
            with self.assertRaises(ValueError): client.call('click', args)
        client.rpc.assert_not_called()

    def test_evidence_write_failure_blocks_next_input(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.BackgroundWatch') as watch:
            watch.return_value.start.return_value.finish.return_value = None
            client = runner.Client.__new__(runner.Client)
            client.output = Path(folder); client.serial = 5; client.session = 'test'
            client.background_fault = None; client.input_fault = None
            client.rpc = Mock(return_value={'content': []})
            args = dict(pid=1, window_id=2, delivery_mode='background', text='x')
            with patch.object(Path, 'write_text', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(OSError, 'disk full'): client.call('type_text', args)
            with self.assertRaisesRegex(RuntimeError, 'further input blocked'): client.call('type_text', args)
            self.assertEqual(client.rpc.call_count, 1)


class CleanupTests(unittest.TestCase):
    def client(self):
        client=runner.Client.__new__(runner.Client)
        client.process=Mock();client.log=Mock();client.lease=Mock()
        return client

    def test_termination_timeout_retains_ownership_until_confirmed_exit(self):
        import subprocess
        client=self.client()
        client.process.wait.side_effect=subprocess.TimeoutExpired('driver',5)
        client.process.poll.return_value=None
        with self.assertRaises(subprocess.TimeoutExpired):client.stop_process()
        client.lease.close.assert_not_called();client.log.close.assert_not_called()
        client.process.wait.side_effect=None;client.process.poll.return_value=0
        client.stop_process()
        client.lease.close.assert_called_once();client.log.close.assert_called_once()

    def test_server_retains_client_when_cleanup_fails(self):
        from mcp_server import Server
        server=Server();client=Mock();server.client=client;server.session='owner'
        client.close.side_effect=TimeoutError('still running')
        with self.assertRaises(TimeoutError):server.close()
        self.assertIs(server.client,client);self.assertEqual(server.session,'owner')
        client.close.side_effect=None;server.close()
        self.assertIsNone(server.client);self.assertIsNone(server.session)


if __name__ == '__main__': unittest.main()
