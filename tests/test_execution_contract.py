import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from desktop_lease import DesktopLease
from run_sequence import Client
from runtime import driver_path


@unittest.skipUnless(os.name == 'nt', 'Windows desktop ownership')
class ExecutionContractTests(unittest.TestCase):
    def test_wrong_driver_never_starts_process(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.subprocess.Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'alternate driver'):
                Client('different-cua.exe', Path(folder))
            launch.assert_not_called()

    def test_duplicate_client_in_same_thread_is_refused(self):
        name = 'Local\\cua-test-' + uuid.uuid4().hex
        lease = DesktopLease(name)
        try:
            with self.assertRaisesRegex(RuntimeError, 'existing client'): DesktopLease(name)
        finally: lease.close()
        DesktopLease(name).close()

    def test_another_process_is_refused_and_crashed_owner_releases(self):
        name = 'Local\\cua-test-' + uuid.uuid4().hex
        code = 'import sys;sys.path.insert(0,sys.argv[1]);from desktop_lease import DesktopLease;l=DesktopLease(sys.argv[2]);print("ready",flush=True);sys.stdin.read()'
        child = subprocess.Popen([sys.executable, '-c', code, str(SCRIPTS), name],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'ready')
            with self.assertRaisesRegex(RuntimeError, 'confirmed exit'): DesktopLease(name)
            child.terminate(); child.wait(timeout=5)
            DesktopLease(name).close()
        finally:
            if child.poll() is None: child.terminate(); child.wait(timeout=5)
            child.stdin.close(); child.stdout.close(); child.stderr.close()

    def test_start_failure_releases_ownership(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.subprocess.Popen', side_effect=OSError('start failed')):
            with self.assertRaisesRegex(OSError, 'start failed'): Client(driver_path(), Path(folder))
        DesktopLease().close()

    def test_existing_evidence_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder, patch('run_sequence.subprocess.Popen') as launch:
            path = Path(folder) / 'driver-stderr.log'; path.write_text('existing')
            with self.assertRaises(FileExistsError): Client(driver_path(), Path(folder))
            self.assertEqual(path.read_text(), 'existing'); launch.assert_not_called()
        DesktopLease().close()


if __name__ == '__main__': unittest.main()
