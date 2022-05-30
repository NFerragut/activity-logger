"""task_checker.py -- Check for any current user activity."""

from datetime import datetime
import logging
import os

from activity import Activity

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
_DEFAULT_INACTIVE_SECONDS = 300
_DEFAULT_MIN_TASK_TIME = 30


class TaskChecker():
    """Manages the activity loggers repeated task loop."""

    def __init__(self, *,
                 min_task_time: int = _DEFAULT_MIN_TASK_TIME,
                 inactive_seconds: int = _DEFAULT_INACTIVE_SECONDS):
        self._activity = Activity()
        self._activity._inactive_seconds = inactive_seconds
        self._activity_start = datetime.now()
        self._last_check = self._activity_start
        self._min_task_time = min_task_time
        self._user_was_active = False
        self._window = None

    def check(self) -> str:
        """Run a check for user activity."""
        message = ''
        try:
            user_is_active = self._activity.user_active()
            if self._user_was_active and user_is_active:
                # user was and is active
                now = datetime.now()
                task_time = self._last_check - self._activity_start
                if task_time.seconds >= self._min_task_time:
                    window = self._activity.get_active_window()
                    if self._window != window:
                        message = self._log(task_time.seconds)
                        self._window = window
                        self._activity_start = now
                self._last_check = now
            elif self._user_was_active and not user_is_active:
                # user was active and is now inactive
                task_time = self._last_check - self._activity_start
                message = '        active --> inactive'
                if task_time.seconds >= self._min_task_time:
                    message = self._log(task_time.seconds) + '\n' + message
                self._user_was_active = False
            elif not self._user_was_active and user_is_active:
                # user was inactive and is now active
                self._window = self._activity.get_active_window()
                activity_start = datetime.now()
                inactive = activity_start - self._last_check
                message = '        inactive --> active'
                if inactive.seconds > 1:
                    message = f'            inactive for {inactive.seconds} seconds\n' + message
                self._activity_start = activity_start
                self._last_check = self._activity_start
                self._user_was_active = True
        # pylint: disable=broad-except; Guarantee handling of whatever error MS Windows throws
        except Exception:
            pass
        return message

    def _log(self, task_seconds) -> str:
        timestamp = self._activity_start.strftime(_DATETIME_FORMAT)
        logging.info('%s\t%1.0f\t%s\t%s\t%s', timestamp, task_seconds,
                     self._window['title'], self._window['path'], self._window['hwnd'])
        app_name = os.path.basename(self._window['path'])
        return f'Logged: {task_seconds:4.0f}s "{self._window["title"]}" ({app_name})'
