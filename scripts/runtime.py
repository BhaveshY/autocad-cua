"""Resolve and verify the plugin's own pinned driver, without global installation."""
import hashlib
import json
import os
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parent.parent

def driver_path():
    if os.name != 'nt' or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('This package requires Windows x64; this host is not qualified.')
    manifest = json.loads((ROOT / 'runtime.json').read_text(encoding='utf-8'))
    driver = ROOT / 'bin' / 'cua-driver.exe'
    actual = hashlib.sha256(driver.read_bytes()).hexdigest()
    if actual != manifest['sha256']:
        raise RuntimeError('Bundled Cua hash mismatch. No driver was launched; restore the verified package.')
    return str(driver)
