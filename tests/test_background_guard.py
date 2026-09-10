import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from background_guard import BackgroundWatch
from run_sequence import Client
from runtime import driver_path


class BackgroundTests(unittest.TestCase):
    def test_overlay_setting_is_local_to_the_owned_mcp_process(self):
        for show,expected in [(False,True),(True,False)]:
            with self.subTest(show=show), tempfile.TemporaryDirectory() as root, patch('run_sequence.subprocess.Popen') as popen, patch.object(Client,'rpc',return_value={}):
                popen.return_value.stdout=[]
                driver=driver_path()
                client=Client(driver,Path(root),show_overlay=show)
                try:
                    argv=popen.call_args.args[0]
                    self.assertEqual(argv[:3],[driver,'mcp','--direct'])
                    self.assertEqual('--no-overlay' in argv,expected)
                finally:client.close()

    def test_transient_change_is_retained_after_return_to_original(self):
        a={'foreground':1,'focus':2}; b={'foreground':3,'focus':4}
        read=Mock(side_effect=[a,b,a])
        watch=BackgroundWatch(read)
        watch.sample(); watch.sample()
        self.assertEqual(watch.change,{'before':a,'after':b})

    def test_focus_change_with_same_foreground_is_detected(self):
        watch=BackgroundWatch(Mock(side_effect=[{'foreground':1,'focus':2},{'foreground':1,'focus':3}]))
        watch.sample()
        self.assertEqual(watch.change['after']['focus'],3)

    def test_observation_error_is_not_success(self):
        watch=BackgroundWatch(Mock(side_effect=[{'foreground':1,'focus':2},OSError('desktop unavailable')]))
        watch.sample()
        self.assertIn('observation_error',watch.change)

    def test_unchanged_state_is_allowed(self):
        watch=BackgroundWatch(lambda: {'foreground':1,'focus':2})
        watch.start()
        self.assertIsNone(watch.finish())

    def client(self,root):
        client=Client.__new__(Client)
        client.session='test';client.output=Path(root);client.serial=5
        client.background_fault=None;client.rpc=Mock(return_value={'content':[]})
        return client

    def test_change_blocks_next_input_but_allows_readback(self):
        with tempfile.TemporaryDirectory() as root, patch('run_sequence.BackgroundWatch') as factory:
            factory.return_value.start.return_value.finish.return_value={'before':{'foreground':1},'after':{'foreground':2}}
            client=self.client(root)
            args=dict(pid=10,window_id=20,delivery_mode='background',text='x')
            with self.assertRaisesRegex(RuntimeError,'may have executed'):client.call('type_text',args)
            self.assertTrue((Path(root)/'background-change.json').exists())
            with self.assertRaisesRegex(RuntimeError,'further input blocked'):client.call('type_text',args)
            self.assertEqual(client.rpc.call_count,1)
            client.call('get_window_state',dict(pid=10,window_id=20))
            self.assertEqual(client.rpc.call_count,2)

    def test_cannot_observe_before_call_sends_no_input(self):
        with tempfile.TemporaryDirectory() as root, patch('run_sequence.BackgroundWatch',side_effect=RuntimeError('unavailable')):
            client=self.client(root)
            with self.assertRaises(RuntimeError):client.call('click',dict(pid=1,window_id=2,delivery_mode='background'))
            client.rpc.assert_not_called()

    def test_client_rejects_unsafe_target_before_rpc(self):
        with tempfile.TemporaryDirectory() as root:
            client=self.client(root)
            base=dict(pid=1,window_id=2,delivery_mode='background')
            for override in [dict(delivery_mode='foreground'),dict(pid=0),dict(window_id=None),dict(target={'kind':'desktop'}),dict(display_id='primary')]:
                with self.assertRaises(ValueError):client.call('click',dict(base,**override))
            client.rpc.assert_not_called()

    def test_rpc_exception_still_finishes_watch_without_replay(self):
        with tempfile.TemporaryDirectory() as root, patch('run_sequence.BackgroundWatch') as factory:
            watch=factory.return_value.start.return_value;watch.finish.return_value=None
            client=self.client(root);client.rpc.side_effect=TimeoutError('uncertain')
            with self.assertRaises(TimeoutError):client.call('click',dict(pid=1,window_id=2,delivery_mode='background'))
            watch.finish.assert_called_once();client.rpc.assert_called_once()

if __name__=='__main__':unittest.main()
