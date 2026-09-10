import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from background_guard import BackgroundWatch


class CoexistenceTests(unittest.TestCase):
    def watch(self):
        return BackgroundWatch(lambda: dict(foreground=10, focus=11))

    def test_another_app_is_allowed(self):
        with patch('background_guard.window_process', side_effect=[200, 100]):
            self.watch().check_target(200, 20)

    def test_same_process_other_window_is_still_in_use(self):
        with patch('background_guard.window_process', side_effect=[200, 200]):
            with self.assertRaisesRegex(RuntimeError, 'foreground use'):
                self.watch().check_target(200, 20)

    def test_reused_window_handle_is_rejected(self):
        with patch('background_guard.window_process', return_value=999):
            with self.assertRaisesRegex(RuntimeError, 'ownership changed'):
                self.watch().check_target(200, 20)

    def test_closed_window_is_rejected(self):
        with patch('background_guard.window_process', side_effect=RuntimeError('gone')):
            with self.assertRaisesRegex(RuntimeError, 'gone'):
                self.watch().check_target(200, 20)

    def test_user_switches_during_preflight(self):
        read = Mock(side_effect=[dict(foreground=10, focus=11), dict(foreground=20, focus=21)])
        with patch('background_guard.window_process', return_value=200):
            with self.assertRaisesRegex(RuntimeError, 'before dispatch'):
                BackgroundWatch(read).check_target(200, 20)

    def test_transient_switch_before_dispatch_is_not_ignored(self):
        watch = self.watch(); watch.change = {'observed': True}
        with patch('background_guard.window_process', return_value=200):
            with self.assertRaisesRegex(RuntimeError, 'before dispatch'):
                watch.check_target(200, 20)


if __name__ == '__main__': unittest.main()
