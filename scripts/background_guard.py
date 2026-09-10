"""Read-only foreground observation; never restores focus or sends input."""
import ctypes
import os
import threading

INPUTS = {'type_text', 'press_key', 'click', 'double_click', 'right_click', 'scroll', 'drag', 'launch_app'}
READS = {'list_apps', 'list_windows', 'get_window_state', 'verify_state'}
LIFECYCLE = {'start_session', 'end_session'}


def window_process(hwnd):
    """Read live HWND ownership without activating or modifying the window."""
    if os.name != 'nt':
        raise RuntimeError('Window ownership requires Windows.')
    from ctypes import wintypes as w
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.IsWindow.argtypes = [w.HWND]
    user.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
    pid = w.DWORD()
    if not user.IsWindow(hwnd) or not user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)) or not pid.value:
        raise RuntimeError('Window no longer exists or its process cannot be observed.')
    return pid.value


def foreground_state():
    if os.name != 'nt':
        raise RuntimeError('Foreground observation requires Windows.')
    from ctypes import wintypes as w
    class Gui(ctypes.Structure):
        _fields_ = [('size', w.DWORD), ('flags', w.DWORD),
                    ('active', w.HWND), ('focus', w.HWND), ('capture', w.HWND),
                    ('menu', w.HWND), ('move', w.HWND), ('caret', w.HWND), ('rect', w.RECT)]
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.GetForegroundWindow.restype = w.HWND
    user.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
    user.GetGUIThreadInfo.argtypes = [w.DWORD, ctypes.POINTER(Gui)]
    hwnd = user.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError('Cannot observe the foreground window; no background input authorized.')
    thread = user.GetWindowThreadProcessId(hwnd, None)
    info = Gui(); info.size = ctypes.sizeof(info)
    if not thread or not user.GetGUIThreadInfo(thread, ctypes.byref(info)):
        raise RuntimeError('Cannot observe foreground keyboard focus.')
    return {'foreground': int(hwnd), 'focus': int(info.focus or 0)}


class BackgroundWatch:
    """Detect observed changes, including transitions back before a call returns.

    Sampling cannot prove absence of shorter transitions, or identify who caused
    a change. Cursor movement by a working user is intentionally not a fault.
    """
    def __init__(self, read=foreground_state, interval=.01):
        self.read, self.interval = read, interval
        self.initial = read()
        self.change = None
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._watch, daemon=True)

    def sample(self):
        try:
            state = self.read()
            if state != self.initial and self.change is None:
                self.change = {'before': self.initial, 'after': state}
        except Exception as error:
            self.change = self.change or {'observation_error': str(error)}

    def _watch(self):
        while not self.stop.wait(self.interval):
            self.sample()

    def start(self):
        self.thread.start()
        return self

    def check_target(self, pid, hwnd):
        if window_process(hwnd) != pid:
            raise RuntimeError('Target window ownership changed; no input sent.')
        current = self.read()
        if current != self.initial or self.change:
            raise RuntimeError('Desktop focus changed before dispatch; no input sent.')
        if window_process(current['foreground']) == pid:
            raise RuntimeError('Target app is in foreground use; no input sent. Resume only after the user leaves that app and its state is rechecked.')

    def finish(self):
        self.stop.set()
        self.thread.join()
        self.sample()
        return self.change
