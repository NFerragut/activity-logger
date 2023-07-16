"""Access information about user activity on the Windows platform"""

import ctypes
from ctypes import Structure, POINTER, WINFUNCTYPE
from ctypes.wintypes import BOOL, UINT, DWORD
import msvcrt
import wmi
import win32gui
import win32process

_INVALID_PID_VALUE = -1
_INVALID_HANDLE_VALUE = -1

class LASTINPUTINFO(Structure):
    """Microsoft Windows structure that holds the time of the last user input event"""
    # pylint: disable=too-few-public-methods; Structure class too simple for __init__()
    _fields_ = [
        ("cbSize", UINT),
        ("dwTime", DWORD)
    ]

class WindowsActivity():
    """Utilities to get user activity on the Windows platform"""

    def __init__(self):
        self._wmi = wmi.WMI()

    @staticmethod
    def get_active_window_handle() -> int:
        """Get the handle (HWND) of the active Microsoft Windows window."""
        # pylint: disable=c-extension-no-member; Allow calls to win32gui methods
        return win32gui.GetForegroundWindow()

    def get_app_path(self, hwnd) -> str:
        """Get the path to the application that owns the window handle"""
        path = ''
        if hwnd != _INVALID_HANDLE_VALUE:
            pid = self._get_process_id(hwnd)
            if pid != _INVALID_PID_VALUE:
                for process in self._wmi.query(
                        f'SELECT ExecutablePath FROM Win32_Process WHERE ProcessId = {pid}'):
                    path = process.ExecutablePath
        return path

    @staticmethod
    def get_keypress() -> str:
        """Get a keypress (if any)"""
        if msvcrt.kbhit():
            return chr(ord(msvcrt.getch()))
        return ''

    @staticmethod
    def get_uptime_ms() -> int:
        """Get the time (ms) that the machine has been running"""
        prototype = WINFUNCTYPE(DWORD)
        paramflags = ()
        # pylint: disable=invalid-name; Use GetTickCount() function name as defined by Microsoft
        GetTickCount = prototype(("GetTickCount", ctypes.windll.kernel32), paramflags)
        return GetTickCount()

    @staticmethod
    def get_user_input_ms() -> int:
        """Get the machine uptime (ms) associated with the last user input"""
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

    @staticmethod
    def get_window_title(hwnd) -> str:
        """Get the window title based on the window handle"""
        if hwnd == _INVALID_HANDLE_VALUE:
            return ''
        # pylint: disable=c-extension-no-member; Allow calls to win32gui methods
        return win32gui.GetWindowText(hwnd)

    @staticmethod
    def _get_process_id(hwnd) -> int:
        # pylint: disable=c-extension-no-member; Allow calls to win32process methods
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
