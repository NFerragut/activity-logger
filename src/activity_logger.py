"""ActivityLogger for logging user activity."""

import json
import msvcrt
import os
import sys
import time

from task_checker import TaskChecker

_CHANGE_ON_TITLE = 'change_on_title'
_DEFAULT_CHANGE_ON_TITLE = ['chrome.exe']
_DEFAULT_INACTIVE_SECONDS = 300
_DEFAULT_LOG_FOLDER = '.'
_DEFAULT_SAMPLE_PERIOD = 3
_INACTIVE_SECONDS = 'inactive_seconds'
_LOG_FOLDER = 'log_folder'
_SAMPLE_PERIOD = 'sample_period'


def main():
    """Run a periodic loop to monitor the machine."""
    config = _read_config()
    checker = TaskChecker(change_on_title=config[_CHANGE_ON_TITLE],
                          inactive_seconds=config[_INACTIVE_SECONDS])
    start_log_message = checker.prepare_logging(config[_LOG_FOLDER])
    print(start_log_message)

    while True:
        message = checker.check()
        if message:
            print(message)

        if _dequeue_key().lower() == 'q':
            sys.exit(0)

        time.sleep(config[_SAMPLE_PERIOD])


# TODO: Create class for config
def _read_config():
    configfile, _ = os.path.splitext(sys.argv[0])
    configfile = os.path.abspath(configfile + '.json')
    config = {
        _SAMPLE_PERIOD: _DEFAULT_SAMPLE_PERIOD,
        _LOG_FOLDER: _DEFAULT_LOG_FOLDER,
        _INACTIVE_SECONDS: _DEFAULT_INACTIVE_SECONDS,
        _CHANGE_ON_TITLE: _DEFAULT_CHANGE_ON_TITLE
    }
    try:
        with open(configfile, encoding='utf-8') as fin:
            config_from_file: dict = json.load(fin)
        config[_LOG_FOLDER] = config_from_file.get(_LOG_FOLDER, _DEFAULT_LOG_FOLDER)
        if _SAMPLE_PERIOD in config_from_file and \
                isinstance(config_from_file[_SAMPLE_PERIOD], int):
            config[_SAMPLE_PERIOD] = max(config_from_file[_SAMPLE_PERIOD], 1)
        if _INACTIVE_SECONDS in config_from_file and \
                isinstance(config_from_file[_INACTIVE_SECONDS], int):
            config[_INACTIVE_SECONDS] = max(config_from_file[_INACTIVE_SECONDS], 60)
        if _CHANGE_ON_TITLE in config_from_file and \
                isinstance(config_from_file[_CHANGE_ON_TITLE], list | tuple):
            config[_CHANGE_ON_TITLE] = tuple(config_from_file[_CHANGE_ON_TITLE])
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


def _dequeue_key():
    key = ''
    if msvcrt.kbhit():
        key = chr(ord(msvcrt.getch()))
    return key


if __name__ == '__main__':
    main()
