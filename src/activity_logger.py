"""ActivityLogger for logging user activity."""

import json
import msvcrt
import os
import sys
import time

import analyze
from task_checker import TaskChecker

_CHANGE_ON_TITLE = 'change_on_title'
_DEFAULT_CHANGE_ON_TITLE = ['chrome.exe']
_DEFAULT_INACTIVE_SECONDS = 300
_DEFAULT_LOG_FOLDER = '.'
_DEFAULT_SAMPLE_PERIOD = 3
_DEFAULT_TASK_TYPES = [
    {
        "name": "Meeting: $1",
        "regex": "^Meet - (.*?) - http.*? - Google Chrome$",
        "action": "collapse"
    },
    {
        "name": "(Lunch)",
        "regex": "IDLE",
        "after": 1125,
        "before": 1400,
        "seconds_min": 600,
        "action": "remove"
    },
    {
        "name": "Away From Desk",
        "regex": "IDLE",
        "seconds_min": 600,
        "action": "sequential"
    },
    {
        "name": "Project Work",
        "action": "sequential"
    }
]
_INACTIVE_SECONDS = 'inactive_seconds'
_LOG_FOLDER = 'log_folder'
_SAMPLE_PERIOD = 'sample_period'
_TASK_TYPES = 'task_types'


def main():
    """Run a periodic loop to monitor the machine."""
    config = _read_config()
    checker = TaskChecker(change_on_title=config[_CHANGE_ON_TITLE],
                          inactive_seconds=config[_INACTIVE_SECONDS])
    if len(sys.argv) > 1:
        filename = checker.get_log_filename(config[_LOG_FOLDER])
        analyze.analyze(sys.argv[1], filename, config[_TASK_TYPES])
        sys.exit(0)
    start_log_message = checker.prepare_logging(config[_LOG_FOLDER])
    print(start_log_message)

    while True:
        message = checker.check()
        if message:
            print(message)

        if _dequeue_key().lower() == 'q':
            sys.exit(0)

        time.sleep(config[_SAMPLE_PERIOD])


def _read_config():
    configfile, _ = os.path.splitext(sys.argv[0])
    configfile = os.path.abspath(configfile + '.json')
    config = {
        _SAMPLE_PERIOD: _DEFAULT_SAMPLE_PERIOD,
        _LOG_FOLDER: _DEFAULT_LOG_FOLDER,
        _INACTIVE_SECONDS: _DEFAULT_INACTIVE_SECONDS,
        _CHANGE_ON_TITLE: _DEFAULT_CHANGE_ON_TITLE,
        _TASK_TYPES: _DEFAULT_TASK_TYPES
    }
    try:
        with open(configfile, encoding='utf-8') as fin:
            config_from_file: dict = json.load(fin)
        config = {**config, **config_from_file}
    except json.JSONDecodeError as error:
        with open(configfile, encoding='utf-8') as fin:
            lines = fin.readlines()
        print(lines[error.lineno - 1].rstrip())
        print(' ' * (error.colno - 1) + '^')
        print(f'Error in "{configfile}" (line {error.lineno}): {str(error.msg)}')
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
