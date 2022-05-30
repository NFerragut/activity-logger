"""task_checker.py -- Check for any current user activity."""

from datetime import datetime, timedelta
import logging
import os

from activity import Activity

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
_MAX_SECONDS_WITHOUT_LOG = 15 * 60


class TaskChecker():
    """Manages the activity loggers repeated task loop."""

    def __init__(self, *, change_on_title: tuple, inactive_seconds: int):
        self._activity = Activity()
        self._activity._inactive_seconds = inactive_seconds
        self._activity_start = datetime.now()
        self._change_on_title = tuple(change_on_title)
        self._last_check = self._activity_start
        self._user_was_active = False
        hwnd = -1
        path = ''
        title = ''
        self._window = (hwnd, path, title)

    def prepare_logging(self, folder) -> str:
        """Prepare to log messages to the output file."""
        os.makedirs(folder, exist_ok=True)
        username = os.getlogin()
        startofweek = self._get_first_day_of_the_week()
        filename = os.path.join(folder, f'{username}-{startofweek}.tab')
        logging.basicConfig(filename=filename, format='%(message)s', level=logging.DEBUG)
        start_time = datetime.now().strftime(_DATETIME_FORMAT)
        logging.info('%s\tActive Seconds\tTitle\tExecutable\tHWND', start_time)
        return f'Logging to {filename}'

    @staticmethod
    def _get_first_day_of_the_week():
        now = datetime.now()
        first_day = now - timedelta(days=now.weekday())
        return first_day.strftime('%Y-%m-%d')

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
            if self._should_log(task_time.seconds, hwnd, path, title):
                message = self._log(self._activity_start, task_time.seconds)
                self._window = (hwnd, path, title)
                self._activity_start = self._last_check
        self._last_check = datetime.now()
        return message

    def _should_log(self, seconds, hwnd, path, title) -> bool:
        _hwnd, _path, _title = self._window
        if _hwnd != hwnd and _path != path:
            return True
        if seconds >= _MAX_SECONDS_WITHOUT_LOG:
            return True
        app_name = os.path.basename(path).lower()
        if app_name in self._change_on_title and _title != title:
            return True
        return False

    def _user_active_to_inactive(self):
        message = '        active --> inactive'
        task_time = self._last_check - self._activity_start
        seconds_since_input = self._activity.seconds_since_input()
        task_seconds = task_time.seconds - seconds_since_input
        if task_seconds > 1:
            logmsg = self._log(self._activity_start, task_seconds)
            message = '\n'.join([logmsg, message])
        self._last_check = datetime.now()
        self._user_was_active = False
        return message

    def _user_inactive_to_active(self) -> str:
        message = '        inactive --> active'
        activity_start = datetime.now()
        inactive = activity_start - self._last_check
        if inactive.seconds > 1:
            self._log(activity_start, inactive.seconds)
            message = f'            inactive for {inactive.seconds} seconds\n{message}'
        self._window = self._activity.get_active_window()
        self._activity_start = activity_start
        self._last_check = activity_start
        self._user_was_active = True
        return message

    def _log(self, activity_start, task_seconds) -> str:
        timestamp = activity_start.strftime(_DATETIME_FORMAT)
        if self._user_was_active:
            hwnd, path, title = self._window
            logging.info('%s\t%1.0f\t%s\t%s\t%s', timestamp, task_seconds,
                         title, path, hwnd)
            app_name = os.path.basename(path)
            message = f'Logged: {task_seconds:4.0f}s "{title}" ({app_name})'
        else:
            message = 'IDLE'
            logging.info('%s\t%1.0f\t%s\t\t', timestamp, task_seconds, message)
        return message
