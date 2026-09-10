"""One cooperating plugin client per Windows session; OS releases crashed owners."""
import ctypes
from ctypes import wintypes as w
import os
import threading

_held = set()
_gate = threading.Lock()


class DesktopLease:
    def __init__(self, name=r'Local\autocad-cua-client-v1'):
        self.name = name
        with _gate:
            if name in _held:
                raise RuntimeError('Another plugin client owns this desktop session. Reuse the existing client.')
        if os.name != 'nt':
            raise RuntimeError('Desktop ownership requires Windows.')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateMutexW.argtypes = [ctypes.c_void_p, w.BOOL, w.LPCWSTR]
        self.kernel.CreateMutexW.restype = w.HANDLE
        self.kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.kernel.WaitForSingleObject.restype = w.DWORD
        self.kernel.ReleaseMutex.argtypes = [w.HANDLE]
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.kernel.CreateMutexW(None, False, name)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        result = self.kernel.WaitForSingleObject(self.handle, 0)
        if result not in (0, 0x80):
            self.kernel.CloseHandle(self.handle)
            self.handle = None
            if result == 0x102:
                raise RuntimeError('Another plugin client owns this desktop session. Keep one GUI worker; wait for its confirmed exit.')
            raise RuntimeError('Cannot establish exclusive desktop ownership.')
        with _gate:
            _held.add(name)

    def close(self):
        if self.handle:
            self.kernel.ReleaseMutex(self.handle)
            self.kernel.CloseHandle(self.handle)
            self.handle = None
            with _gate:
                _held.discard(self.name)
