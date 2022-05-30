"""task_checker.py -- Check for any current user activity."""

from datetime import datetime
import logging
import os

from activity import Activity

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class TaskChecker():
    """Manages the activity loggers repeated task loop."""

    def __init__(self, *, change_on_title: tuple, inactive_seconds: int):
        self._activity = Activity()
        self._activity._inactive_seconds = inactive_seconds
        self._activity_start = datetime.now()
        self._change_on_title = tuple(change_on_title)
        self._hwnd = -1
        self._last_check = self._activity_start
        self._path = ''
        self._title = ''
        self._user_was_active = False

    def check(self) -> str:
        """Run a check for user activity."""
        message = ''
        try:
            user_is_active = self._activity.user_active()
            if self._user_was_active and user_is_active:
                message = self._user_active()
            elif self._user_was_active and not user_is_active:
                message = self._user_active_to_inactive()
            elif not self._user_was_active and user_is_active:
                message = self._user_inactive_to_active()
        # pylint: disable=broad-except; Guarantee handling of whatever error MS Windows throws
        except Exception:
            message = ''
        return message

    def _user_active(self):
        task_time = self._last_check - self._activity_start
        if task_time.seconds > 1:
            hwnd, path, title = self._activity.get_active_window()
            if self._should_log(hwnd, path, title):
                message = self._log(task_time.seconds)
                self._hwnd = hwnd
                self._path = path
                self._title = title
                self._activity_start = self._last_check
        self._last_check = datetime.now()
        return message

    def _should_log(self, hwnd, path, title) -> bool:
        if self._hwnd != hwnd:
            return True
        app_name = os.path.basename(path).lower()
        if app_name in self._change_on_title and self._title != title:
            return True
        return False

    def _user_active_to_inactive(self):
        message = '        active --> inactive'
        task_time = self._last_check - self._activity_start
        seconds_since_input = self._activity.seconds_since_input()
        task_seconds = task_time.seconds - seconds_since_input
        if task_seconds > 1:
            message = self._log(task_seconds) + '\n' + message
        self._last_check = datetime.now()
        self._user_was_active = False
        return message

    def _user_inactive_to_active(self) -> str:
        message = '        inactive --> active'
        activity_start = datetime.now()
        inactive = activity_start - self._last_check
        if inactive.seconds > 1:
            message = f'            inactive for {inactive.seconds} seconds\n' + message
        self._hwnd, self._path, self._title = self._activity.get_active_window()
        self._activity_start = activity_start
        self._last_check = activity_start
        self._user_was_active = True
        return message

    def _log(self, task_seconds) -> str:
        timestamp = self._activity_start.strftime(_DATETIME_FORMAT)
        logging.info('%s\t%1.0f\t%s\t%s\t%s', timestamp, task_seconds,
                     self._title, self._path, self._hwnd)
        app_name = os.path.basename(self._path)
        return f'Logged: {task_seconds:4.0f}s "{self._title}" ({app_name})'
