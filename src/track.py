"""ActivityLogger for logging user activity."""

from argparse import ArgumentParser
from datetime import timedelta
from logging import info
from pathlib import Path
import sys
import time

from logfile import LogFile
from windows_activity import WindowsActivity
from record import Record, HEADER_TEXT

_INACTIVE_AFTER_SECONDS = 7.0 * 60
_LOG_FOLDER = '.'
_SECONDS_BETWEEN_CHECKS = 2.0

def parse_arguments():
    """Get user-selected options for tracking user activity"""
    parser = ArgumentParser()
    parser.description = """Create a log of user's weekly activity"""
    parser.add_argument('-f', '--folder',
                        type=str, default=_LOG_FOLDER,
                        help='Folder path for log files')
    parser.add_argument('-i', '--inactive',
                        type=int, default=_INACTIVE_AFTER_SECONDS,
                        help='User inactive after specified seconds')
    parser.add_argument('-s', '--sample',
                        type=float, default=_SECONDS_BETWEEN_CHECKS,
                        help='Seconds between checking for user activity')
    return parser.parse_args()

def main():
    """Run a periodic loop to monitor the user's activity"""
    args = parse_arguments()
    LogFile.prepare(args.folder)
    info('\n%s', HEADER_TEXT)

    user_activity = Record()
    winact = WindowsActivity()

    while True:
        user_activity = _check_user_activity(user_activity, winact, args.inactive)
        _quit_on_key()
        time.sleep(args.sample)

def _check_user_activity(user_activity:Record, winact:WindowsActivity, inactive:int):
    # Check for any new user activity
    current = _get_current_record(winact, inactive)

    active_changed = user_activity.active != current.active
    if active_changed:
        print(current.active_state)
        if not current.active:
            start = current.start
            start -= timedelta(seconds=inactive)
            current.start = start

    window_changed = (user_activity.hwnd != current.hwnd or
                        user_activity.title != current.title or
                        user_activity.app != current.app)
    if active_changed or window_changed:
        print(current.raw_text())
        info(current.raw_text())
        return current
    return user_activity

def _quit_on_key():
    # Check if the user pressed the 'q' key to quit
    keypress = WindowsActivity.get_keypress()
    if keypress in ['q', 'Q']:
        sys.exit(0)
    if keypress:
        print("Press 'q' to quit")

def _get_current_record(winact:WindowsActivity, inactive:int) -> Record:
    uptime = winact.get_uptime_ms()
    user_input_ms = winact.get_user_input_ms()
    idle_ms = uptime - user_input_ms
    active = idle_ms < (1000 * inactive)
    hwnd = winact.get_active_window_handle()
    title = winact.get_window_title(hwnd)
    app = Path(winact.get_app_path(hwnd)).name.lower()
    return Record(active, hwnd, title, app)

if __name__ == '__main__':
    main()
