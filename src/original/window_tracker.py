"""window_tracker.py

Creates a history of active windows and their time stamps"""

import sys
import ctypes
from ctypes.wintypes import DWORD, HANDLE, HWND, LONG

import win32con

# These are the events that will trigger the WindowTracker to check the current active window.
_EVENT_TYPES = {
    win32con.EVENT_SYSTEM_FOREGROUND: "Foreground",
    win32con.EVENT_OBJECT_FOCUS: "Focus",
    win32con.EVENT_OBJECT_SHOW: "Show",
    win32con.EVENT_SYSTEM_DIALOGSTART: "Dialog",
    win32con.EVENT_SYSTEM_CAPTURESTART: "Capture",
    win32con.EVENT_SYSTEM_MINIMIZEEND: "UnMinimize"
}

class WindowTracker:
    """Keeps a log of active windows"""

    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.ole32 = ctypes.windll.ole32
        self.user32 = ctypes.windll.user32

    def get_process_id(self, hwnd:HWND, thread_id:DWORD) -> DWORD:
        """Get the process ID based on the Window handle and thread ID"""

        process_id = None

        thread_flag = getattr(win32con, 'THREAD_QUERY_LIMITED_INFORMATION',
                              win32con.THREAD_QUERY_INFORMATION)
        thread = self.kernel32.OpenThread(thread_flag, 0, thread_id)

        if thread:
            # Try getting the Process ID from the Thread ID
            try:
                pid = self.kernel32.GetProcessIdOfThread(thread)
                if pid:
                    process_id = pid
                else:
                    print(f'Could not get the PID for thread {thread:#x}')
            finally:
                self.kernel32.CloseHandle(thread)
        elif hwnd:
            # Try getting the Process ID from the Window Handle
            pid = DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid:
                process_id = pid.value
            else:
                print(f'Could not get PID from Window Handle {hwnd:#x}')

        return process_id

    def get_process_filename(self, process_id):
        """Get the name of the application that generated the event"""
        filename = None

        process_flag = getattr(win32con, 'PROCESS_QUERY_LIMITED_INFORMATION',
                               win32con.PROCESS_QUERY_INFORMATION)
        process = self.kernel32.OpenProcess(process_flag, 0, process_id)
        if process:
            try:
                filename_buffer_size = DWORD(4096)
                filename_buffer = ctypes.create_unicode_buffer(filename_buffer_size.value)
                self.kernel32.QueryFullProcessImageNameW(process, 0, ctypes.byref(filename_buffer),
                                                         ctypes.byref(filename_buffer_size))
                filename = filename_buffer.value
            finally:
                self.kernel32.CloseHandle(process)
        else:
            print(f'Cannot open process {process_id:#x}')

        return filename

