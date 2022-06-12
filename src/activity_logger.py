"""ActivityLogger for logging user activity."""

import json
import locale
import msvcrt
import os
import re
import sys
import time

from record import Record
from time_entry import TimeEntry
from task_checker import TaskChecker

_CHANGE_ON_TITLE = 'change_on_title'
_DEFAULT_CHANGE_ON_TITLE = ['chrome.exe']
_DEFAULT_INACTIVE_SECONDS = 300
_DEFAULT_LOG_FOLDER = '.'
_DEFAULT_SAMPLE_PERIOD = 3
_DEFAULT_TASK_TYPES = {
    "Meeting": {
        "title": "Meet - (.*?)(?: - http:.*?)? - Google Chrome",
        "action": "collapse",
        "max_seconds": 9000
    }
}
_GROUP1 = '$1'
_INACTIVE_SECONDS = 'inactive_seconds'
_LOG_FOLDER = 'log_folder'
_SAMPLE_PERIOD = 'sample_period'
_TASK_TYPES = 'filters'
_UNKNOWN_TASK = {
    'name': 'Unknown Task',
    'regex': r'.',
    'action': 'default'
}


def main():
    """Run a periodic loop to monitor the machine."""
    config = _read_config()
    checker = TaskChecker(change_on_title=config[_CHANGE_ON_TITLE],
                          inactive_seconds=config[_INACTIVE_SECONDS])
    if len(sys.argv) > 1:
        filename = checker.get_log_filename(config[_LOG_FOLDER])
        report = evaluate_log(filename, config)
        command = sys.argv[1].lower()
        if command.startswith(('col', 'tab')):
            print('Table coming soon:')
            print('| Task | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Detail |')
        else:
            for task in report:
                print(str(task), file=sys.stdout)
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


# TODO: Create class for config
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
        print(f'Error in "{configfile}": {str(error.msg)}')
        sys.exit(1)
    except FileNotFoundError:
        with open(configfile, 'w', encoding='utf-8') as fout:
            json.dump(config, fout, indent=2)
    return config


def evaluate_log(filename, config) -> list:
    """Evaluate a log file to extract times for hour logging."""
    records = _read_log_file(filename)
    for record in records:
        _identify_record(record, config[_TASK_TYPES])
    report = []
    next_index = 0
    for index, record in enumerate(records):
        if record.is_heading or record.is_idle:
            continue
        if index < next_index:
            continue
        active_task = TimeEntry(index, record)
        next_index = active_task.find_next_index(records)
        report.append(active_task)
    return report


def _read_log_file(filename):
    encoding = locale.getpreferredencoding(False)
    records = []
    with open(filename, 'rt', encoding=encoding) as fin:
        for line in fin:
            if line:
                records.append(Record(line.strip()))
    return records


def _identify_record(record: Record, tests: dict):
    """Determine which test matches the specified record."""
    for test in tests:
        name: str = test['name']
        regex: str = test['regex']
        if found := re.search(regex, record.title):
            if _GROUP1 in name:
                name = name.replace(_GROUP1, found[1])
            record.textout = name
            record.action = test['action']
            return
    record.textout = _UNKNOWN_TASK['name']
    record.action = 'sequential'


def _dequeue_key():
    key = ''
    if msvcrt.kbhit():
        key = chr(ord(msvcrt.getch()))
    return key


if __name__ == '__main__':
    main()
