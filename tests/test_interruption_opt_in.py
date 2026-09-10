import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_sequence import Client
from mcp_server import Server

class InterruptionTests(unittest.TestCase):
    def client(self, folder, allowed):
        c=Client.__new__(Client);c.allow_interruption=allowed;c.input_fault=None;c.background_fault=None
        c.output=Path(folder);c.serial=1;c.session='test';c.rpc=Mock(return_value={'structuredContent':{'effect':'unverifiable'}})
        return c

    def test_default_rejects_foreground_before_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            c=self.client(folder,False)
            with self.assertRaises(ValueError):c.call('click',dict(pid=1,window_id=2,delivery_mode='foreground',x=1,y=1))
            c.rpc.assert_not_called()

    def test_opt_in_allows_focus_change_but_records_it(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.BackgroundWatch') as watch, patch('run_sequence.window_process',return_value=1):
            watch.return_value.start.return_value.finish.return_value={'before':{'foreground':3},'after':{'foreground':2}}
            c=self.client(folder,True);c.call('click',dict(pid=1,window_id=2,delivery_mode='foreground',x=1,y=1))
            c.rpc.assert_called_once();self.assertIsNone(c.background_fault)
            self.assertTrue(json.loads((Path(folder)/'background-change.json').read_text())['allow_interruption'])

    def test_opt_in_still_rejects_wrong_owner(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.BackgroundWatch') as watch, patch('run_sequence.window_process',return_value=99):
            watch.return_value.start.return_value.finish.return_value=None
            c=self.client(folder,True)
            with self.assertRaisesRegex(RuntimeError,'ownership'):c.call('click',dict(pid=1,window_id=2,delivery_mode='foreground',x=1,y=1))
            c.rpc.assert_not_called()

    def test_opt_in_does_not_clear_dispatch_failures(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.BackgroundWatch') as watch, patch('run_sequence.window_process',return_value=1):
            watch.return_value.start.return_value.finish.return_value=None
            c=self.client(folder,True);c.rpc.return_value={'isError':True}
            with self.assertRaises(RuntimeError):c.call('click',dict(pid=1,window_id=2,delivery_mode='foreground',x=1,y=1))
            with self.assertRaisesRegex(RuntimeError,'Earlier input'):c.call('click',dict(pid=1,window_id=2,delivery_mode='foreground',x=1,y=1))
            c.rpc.assert_called_once()

    def test_session_opt_in_rejects_truthy_strings(self):
        with self.assertRaises(ValueError):Server().call('start_session',{'allow_interruption':'true'})

if __name__=='__main__':unittest.main()
