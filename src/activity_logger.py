"""ActivityLogger for logging user activity."""

from datetime import datetime, timedelta
import json
import logging
import msvcrt
import os
import sys
import time

from activity import Activity

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
_INACTIVE_SECONDS = 'inactive_seconds'
_LOG_FOLDER = 'log_folder'
_LOG_RESOLUTION = 'log_resolution'
_SAMPLE_PERIOD = 'sample_period'
_DEFAULT_LOG_FOLDER = 'C:/Data/ActivityLogger'


def main():
    """Run a periodic loop to monitor the machine."""
    config = _read_config()
    _prepare_logging(config[_LOG_FOLDER])

    activity = Activity()
    activity.inactive_seconds = config[_INACTIVE_SECONDS]
    timestamp = datetime.now()
    user_active = activity.user_active()
    window = {}
    while True:
        sleep_time = datetime.now()
        time.sleep(config[_SAMPLE_PERIOD])

        if msvcrt.kbhit():
            msvcrt.getch()
            sys.exit(0)

        if activity.user_active():
            new_window = activity.get_active_window()
            if user_active:
                # User is active
                if window != new_window:
                    active = sleep_time - timestamp
                    if active.seconds >= config[_LOG_RESOLUTION]:
                        _log(timestamp, active.seconds, window)
                        timestamp = sleep_time
                    elif window:
                        app_name = os.path.basename(window['path'])
                        print(f'        {active.seconds:4}s "{window["title"]}" ({app_name})')
                    window = new_window
            else:
                # User was inactive and is now active.
                print('  -->  User is now active')
                user_active = True
                window = new_window
                timestamp = sleep_time
        else:
            if user_active:
                # User was active and is now inactive.
                print('  -->  User is now inactive')
                active = sleep_time - timestamp
                active_seconds = active.seconds - activity.seconds_since_input()
                if active_seconds >= config[_LOG_RESOLUTION]:
                    _log(timestamp, active_seconds, window)
                else:
                    app_name = os.path.basename(window['path'])
                    print(f'        {active_seconds:4.0f}s "{window["title"]}" ({app_name})')
                timestamp = sleep_time
                user_active = False


def _read_config():
    configfile, _ = os.path.splitext(sys.argv[0])
    configfile = os.path.abspath(configfile + '.json')
    config = {
        _SAMPLE_PERIOD: 6,
        _LOG_FOLDER: _DEFAULT_LOG_FOLDER,
        _LOG_RESOLUTION: 30,
        _INACTIVE_SECONDS: 300
    }
    try:
        with open(configfile, encoding='utf-8') as fin:
            config_from_file: dict = json.load(fin)
        config[_LOG_FOLDER] = config_from_file.get(_LOG_FOLDER, _DEFAULT_LOG_FOLDER)
        if _SAMPLE_PERIOD in config_from_file and \
                isinstance(config_from_file[_SAMPLE_PERIOD], int):
            config[_SAMPLE_PERIOD] = max(config_from_file[_SAMPLE_PERIOD], 1)
        if _LOG_RESOLUTION in config_from_file and \
                isinstance(config_from_file[_LOG_RESOLUTION], int):
            config[_LOG_RESOLUTION] = max(config_from_file[_LOG_RESOLUTION], 1)
        if _INACTIVE_SECONDS in config_from_file and \
                isinstance(config_from_file[_INACTIVE_SECONDS], int):
            config[_INACTIVE_SECONDS] = max(config_from_file[_INACTIVE_SECONDS], 60)
    except json.JSONDecodeError as error:
        with open(configfile, encoding='utf-8') as fin:
            lines = fin.readlines()
        print(lines[error.lineno - 1].rstrip())
        print(' ' * (error.colno - 1) + '^')
        print(f'Error in "{configfile}": {str(error.msg)}')
        sys.exit(1)
    except FileNotFoundError:
        with open(configfile, 'w', encoding='utf-8') as fout:
            json.dump(config, fout, indent=2)
    return config


def _prepare_logging(folder):
    os.makedirs(folder, exist_ok=True)
    username = os.getlogin()
    startofweek = _get_first_day_of_the_week()
    filename = os.path.join(folder, f'{username}-{startofweek}.log')
    logging.basicConfig(filename=filename, format='%(message)s', level=logging.DEBUG)
    start_time = datetime.now().strftime(_DATETIME_FORMAT)
    logging.info('%s\tActive Seconds\tTitle\tPath\tHWND', start_time)
    print(f'Logging to {filename}')


def _get_first_day_of_the_week():
    now = datetime.now()
    first_day = now - timedelta(days=now.weekday())
    return first_day.strftime('%Y-%m-%d')


def _log(timestamp, active_seconds, window):
    ts_text = timestamp.strftime(_DATETIME_FORMAT)
    logging.info('%s\t%1.0f\t%s\t%s\t%s', ts_text, active_seconds,
                 window['title'], window['path'], window['hwnd'])
    app_name = os.path.basename(window['path'])
    print(f'Logged: {active_seconds:4.0f}s "{window["title"]}" ({app_name})')


if __name__ == '__main__':
    main()
