"""Access to user activity"""

import ctypes
from ctypes import Structure, POINTER, WINFUNCTYPE
from ctypes.wintypes import BOOL, UINT, DWORD
import wmi
import win32gui
import win32process

_DEFAULT_INACTIVE_SECONDS = 300
INVALID_PID_VALUE = -1
INVALID_HANDLE_VALUE = -1


class Activity():
    """Activity of the user in Windows."""

    def __init__(self):
        self._ms_at_last_activity = 0
        self._wmi = wmi.WMI()
        self._inactive_seconds = _DEFAULT_INACTIVE_SECONDS

    @property
    def inactive_seconds(self) -> int:
        """Get the number of seconds without user activity before assuming an inactive state."""
        return self._inactive_seconds

    @inactive_seconds.setter
    def inactive_seconds(self, value: int):
        """Set the number of seconds without user activity before assuming an inactive state."""
        if isinstance(value, int) and value > 60:
            self._inactive_seconds = value

    def user_active(self) -> bool:
        """True if the user is actively using the computer."""
        return self.seconds_since_input() < self._inactive_seconds

    def seconds_since_input(self) -> int:
        """Get the number of seconds since the last user input."""
        self._ms_at_last_activity = self._get_last_event_time()
        milliseconds = self._get_millisecond_uptime()
        ms_since_input = milliseconds - self._ms_at_last_activity
        return ms_since_input / 1000

    def get_active_window(self) -> dict:
        """Get information about the active window."""
        app_title = None
        app_path = None
        # app_name = None
        hwnd = self.get_active_window_handle()
        if hwnd != INVALID_HANDLE_VALUE:
            app_title = self._get_window_title(hwnd)
            pid = self._get_process_id(hwnd)
            if pid != INVALID_PID_VALUE:
                app_path = self._get_app_path(pid)
                # app_name = self._get_app_name(pid)
        return {'title': app_title, 'path': app_path, 'hwnd': hwnd}

    @staticmethod
    def get_active_window_handle() -> int:
        """Get the handle (HWND) of the active Microsoft Windows window."""
        # pylint: disable=c-extension-no-member; Allow calls to win32gui methods
        return win32gui.GetForegroundWindow()

    @staticmethod
    def _get_process_id(hwnd) -> int:
        # pylint: disable=c-extension-no-member; Allow calls to win32process methods
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid

    @staticmethod
    def _get_window_title(hwnd) -> str:
        # pylint: disable=c-extension-no-member; Allow calls to win32gui methods
        return win32gui.GetWindowText(hwnd)

    def _get_app_path(self, pid) -> str:
        path = ''
        for process in self._wmi.query('SELECT ExecutablePath FROM Win32_Process WHERE '
                                        f'ProcessId = {pid}'):
            path = process.ExecutablePath
        return path

    def _get_app_name(self, pid) -> str:
        name = ''
        for process in self._wmi.query('SELECT Name FROM Win32_Process WHERE '
                                        f'ProcessId = {pid}'):
            name = process.Name
        return name

    @staticmethod
    def _get_millisecond_uptime() -> int:
        prototype = WINFUNCTYPE(DWORD)
        paramflags = ()
        # pylint: disable=invalid-name; Use GetTickCount() function name as defined by Microsoft
        GetTickCount = prototype(("GetTickCount", ctypes.windll.kernel32), paramflags)
        return GetTickCount()

    @staticmethod
    def _get_last_event_time() -> int:
        prototype = WINFUNCTYPE(BOOL, POINTER(LASTINPUTINFO))
        paramflags = ((3, "plii"),)
        # pylint: disable=invalid-name; Use GetLastInputInfo() function name as defined by Microsoft
        GetLastInputInfo = prototype(("GetLastInputInfo", ctypes.windll.user32), paramflags)

        last_input_info = LASTINPUTINFO()
        # pylint: disable=attribute-defined-outside-init; Structure classes do not use __init__()
        # pylint: disable=invalid-name; Use cbSize structure member name as defined by Microsoft
        last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        assert 0 != GetLastInputInfo(last_input_info)
        return last_input_info.dwTime


class LASTINPUTINFO(Structure):
    # pylint: disable=too-few-public-methods; Structure class too simple for __init__()
    """Microsoft Windows structure that holds the time of the last input event."""
    _fields_ = [
        ("cbSize", UINT),
        ("dwTime", DWORD)
    ]
