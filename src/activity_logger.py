"""ActivityLogger for logging user activity."""

from argparse import ArgumentParser
from datetime import datetime, timedelta
from glob import glob
import json
import locale
import msvcrt
import os
import re
import sys
import time

from task_checker import TaskChecker
from time_entry import TimeEntry

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
    args = _parse_args()
    config = _read_config()
    analyze(args, config)
    # if args.analyze:
    #     analyze(args, config)
    # else:
    #     logging_loop(config)


def _parse_args():
    parser = ArgumentParser(prog='ActivityLogger', description='Log user computer activity')
    parser.add_argument('-a', '--analyze',
                        action='store_true',
                        help='analyze a log file')
    parser.add_argument('-w', '--weeks-ago',
                        help='name of the log file to analyze')
    args = parser.parse_args()
    return args


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
        config = { **config, **config_from_file }
        # config[_LOG_FOLDER] = config_from_file.get(_LOG_FOLDER, _DEFAULT_LOG_FOLDER)
        # if _SAMPLE_PERIOD in config_from_file and \
        #         isinstance(config_from_file[_SAMPLE_PERIOD], int):
        #     config[_SAMPLE_PERIOD] = max(config_from_file[_SAMPLE_PERIOD], 1)
        # if _INACTIVE_SECONDS in config_from_file and \
        #         isinstance(config_from_file[_INACTIVE_SECONDS], int):
        #     config[_INACTIVE_SECONDS] = max(config_from_file[_INACTIVE_SECONDS], 60)
        # if _CHANGE_ON_TITLE in config_from_file and \
        #         isinstance(config_from_file[_CHANGE_ON_TITLE], list | tuple):
        #     config[_CHANGE_ON_TITLE] = tuple(config_from_file[_CHANGE_ON_TITLE])
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


def analyze(args, config):
    """Analyze an existing activity log."""
    print(f'analyze = "{args.analyze}"')
    print(f'weeks_ago = "{args.weeks_ago}"')
    log_file = _find_log_file(config[_LOG_FOLDER], args.weeks_ago)
    print(f'log_file = "{log_file}"')
    time_entries = _read_log_file(log_file)
    _apply_filters(time_entries, config)
    for entry in time_entries:
        print(f'{entry.start}\t{entry.seconds:1.0f}\t{entry.title}\t'
              f'{entry.executable}\t{entry.hwnd}')


def _find_log_file(folder, weeks_ago):
    folder = os.path.abspath(folder)
    days_ago = 7 * int(weeks_ago)
    now = datetime.now()
    first_day_ts = now - timedelta(days=now.weekday() + days_ago)
    first_day = first_day_ts.strftime('%Y-%m-%d')
    log_file = glob(f'*-{first_day}.tab', root_dir=folder)
    if len(log_file) == 1:
        return log_file[0]
    print(f'ERROR: Did not find exactly 1 file for the week of {first_day}')
    return ''


def _read_log_file(log_file) -> list:
    """Read the log file into a list of tuples."""
    encoding = locale.getpreferredencoding(False)
    with open(log_file, 'rt', encoding=encoding) as fin:
        lines = fin.readlines()
    time_entries = [TimeEntry(line.split('\t')) for line in lines]
    return time_entries


def _apply_filters(time_entries, config):
    for scanner in config['scanners']:
        _apply_filter(time_entries, scanner)


def _apply_filter(time_entries, scanner):
    search = scanner['search']
    list_changed = True
    start_index = 0
    while list_changed:
        list_changed = False
        for index in range(start_index, len(time_entries)):
            entry = time_entries[index]
            if re.search(search, entry.title):
                action = scanner['action']
                list_changed = _ACTIONS[action](time_entries, scanner, index)
            if list_changed:
                start_index = index + scanner['index_offset']
                break


def _compress_times(time_entries):
    for index in range(len(time_entries) - 1):
        te1 = time_entries[index]
        te2 = time_entries[index + 1]
        difference = te2.start - te1.start
        seconds = difference.total_seconds()
        seconds_error = abs(te1.seconds - seconds)
        if seconds_error > 3:
            print(te1)
            print(f'{te2.start}\t{seconds:1.0f} expected')


def logging_loop(config):
    """Run a periodic loop to monitor the computer usage."""
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


def _dequeue_key():
    key = ''
    if msvcrt.kbhit():
        key = chr(ord(msvcrt.getch()))
    return key


def collapse_same_title(time_entries, scanner, index):
    """Collapse all entries with the same title."""
    te_first: TimeEntry = time_entries[index]
    first_index = index
    te_last: TimeEntry = te_first
    last_index = index
    for index in range(first_index + 1, len(time_entries)):
        te_next: TimeEntry = time_entries[index]
        if te_first.title == te_next.title:
            te_last = te_next
            last_index = index
        else:
            gap = te_next.stop - te_last.stop
            if gap.total_seconds() > scanner['max_gap']:
                break
    if first_index == last_index:
        return False
    difference = te_last.stop - te_first.start
    te_first.seconds = difference.total_seconds()
    del time_entries[first_index + 1:last_index + 1]
    return True


def combine_adjacent(time_entries, _, index):
    """Combine adjacent entries with the same title"""
    te_first: TimeEntry = time_entries[index]
    first_index = index
    for index in range(first_index + 1, len(time_entries)):
        te_next: TimeEntry = time_entries[index]
        next_index = index
        if te_first.title != te_next.title:
            break
    if first_index + 1 == next_index:
        return False
    difference = te_next.start - te_first.start
    te_first.seconds = difference.total_seconds()
    del time_entries[first_index + 1:next_index]
    return True


def discard(time_entries, scanner, index):
    """Discard the selected time entry from the list."""
    te_discard: TimeEntry = time_entries[index]
    if te_discard.seconds > scanner['max']:
        return False
    if index > 0:
        te_prev = time_entries[index - 1]
        te_prev.seconds += te_discard.seconds
    del time_entries[index:index+1]
    return True


def collapse(time_entries, scanner, index):
    """Collapse all entries with a matching title."""
    te_first: TimeEntry = time_entries[index]
    first_index = index
    next_index = first_index + 1
    for index in range(first_index + 1, len(time_entries)):
        te_next: TimeEntry = time_entries[index]
        next_index = index
        if not re.search(scanner['search'], te_next.title):
            break
    if first_index + 1 == next_index:
        return False
    difference = te_next.start - te_first.start
    te_first.seconds = difference.total_seconds()
    del time_entries[first_index + 1:next_index]
    return True



_ACTIONS = {
    "collapse_same_title": collapse_same_title,
    "combine_adjacent": combine_adjacent,
    "discard": discard,
    "collapse": collapse
}


if __name__ == '__main__':
    main()
