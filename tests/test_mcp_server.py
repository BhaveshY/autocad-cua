import json
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from mcp_server import Server, main
from run_sequence import Client


class McpTests(unittest.TestCase):
    def test_invalid_envelope_does_not_break_next_request(self):
        incoming = 'null\n[]\n{broken\n{"jsonrpc":"2.0","id":4,"method":"ping"}\n'
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO(incoming)), patch('sys.stdout', output):
            main()
        replies = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertTrue(all('error' in reply for reply in replies[:3]))
        self.assertEqual(replies[3], {'jsonrpc': '2.0', 'id': 4, 'result': {}})

    def test_instructions_need_no_driver_or_shell(self):
        with patch('mcp_server.Client') as client:
            text = Server().call('instructions', {'topic': 'computer-use'})
            self.assertTrue(text['structuredContent']['instructions'])
            client.assert_not_called()

    def test_no_arbitrary_instruction_paths(self):
        with self.assertRaises(ValueError): Server().call('instructions', {'topic': '../../private'})

    def test_no_write_without_owned_session(self):
        with self.assertRaisesRegex(RuntimeError, 'start_session'):
            Server().call('type_text', dict(session='wrong', pid=1, window_id=2, delivery_mode='background', text='x'))

    def test_wrong_session_never_reaches_client(self):
        server = Server(); server.client = Mock(); server.session = 'owner'
        with self.assertRaisesRegex(RuntimeError, 'start_session'):
            server.call('end_session', {'session': 'other'})
        server.client.close.assert_not_called()

    def test_second_worker_cannot_take_over(self):
        server = Server(); server.client = Mock(); server.session = 'owner'
        with self.assertRaisesRegex(RuntimeError, 'already owns'): server.call('start_session', {})
        self.assertEqual(server.session, 'owner')

    def test_server_preserves_background_guards(self):
        server = Server(); server.session = 'owner'
        client = Client.__new__(Client); client.background_fault = None; client.input_fault = None
        client.rpc = Mock(); server.client = client
        for delivery in ['foreground', 'auto']:
            with self.assertRaises(ValueError):
                server.call('type_text', dict(session='owner', pid=1, window_id=2, delivery_mode=delivery, text='x'))
        client.rpc.assert_not_called()

    def test_override_and_unadvertised_tool_rejected(self):
        server = Server(); server.client = Mock(); server.session = 'owner'
        with self.assertRaises(ValueError): server.call('get_window_state', dict(session='owner', pid=1, window_id=2, target={'kind': 'desktop'}))
        with self.assertRaises(ValueError): server.call('bring_to_front', {})
        server.client.call.assert_not_called()

    def test_correct_session_uses_existing_client_and_returns_images(self):
        server = Server(); server.session = 'owner'; server.client = Mock()
        response = {'content': [{'type': 'image', 'mimeType': 'image/png', 'data': 'test'}]}
        server.client.call.return_value = (response, 1)
        self.assertEqual(server.call('get_window_state', dict(session='owner', pid=1, window_id=2)), response)
        server.client.call.assert_called_once_with('get_window_state', dict(pid=1, window_id=2))

    def test_close_releases_workflow_without_app_action(self):
        server = Server(); client = Mock(); server.client = client; server.session = 'owner'
        self.assertFalse(server.call('end_session', {'session': 'owner'})['structuredContent']['app_closed'])
        client.close.assert_called_once(); client.call.assert_not_called(); self.assertIsNone(server.client)

    def test_launch_requires_exact_executable_and_minimized(self):
        client = Client.__new__(Client); client.background_fault = None; client.input_fault = None; client.rpc = Mock()
        for args in [{}, {'path': 'thunderbird.exe', 'start_minimized': True},
                     {'path': sys.executable, 'start_minimized': False},
                     {'path': sys.executable, 'start_minimized': True, 'additional_arguments': ['-c', 'x']}]:
            with self.assertRaises(ValueError): client.call('launch_app', args)
        client.rpc.assert_not_called()


if __name__ == '__main__': unittest.main()
