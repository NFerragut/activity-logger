"""Routines to analyze the user activity data."""

from datetime import datetime, timedelta
import locale
import re
import sys

from record import Record
from time_entry import TimeEntry, MAX_GAP_SECONDS

_BANNER_WIDTH = 40
_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
_DEFAULT_ACTION = 'sequential'
_GROUP1 = '$1'
_MAX_NAME_COLUMN_WIDTH = 40
_NAME_COLUMN_TITLE = 'Time Entry Name'
_UNKNOWN_TASK_NAME = 'Unknown Task'
_WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def analyze(command: str, filename: str, task_types: dict):
    """Analyze the user activity data."""
    records = read_activity_log(filename)
    remove_headings(records)
    for record in records:
        identify_record(record, task_types)
    entries = group_records(records)
    report(command, entries)


def read_activity_log(filename):
    """Read the specified activity log."""
    records = []
    encoding = locale.getpreferredencoding(False)
    with open(filename, 'rt', encoding=encoding) as fin:
        for line in fin:
            if line:
                fields = line.split('\t')
                fields.extend(['', '', '', ''])
                start = datetime.strptime(fields[0], _DATETIME_FORMAT)
                record = Record(start, fields[1], fields[2], fields[3], fields[4])
                records.append(record)
    return records


def remove_headings(records: list[Record]):
    """Remove all the records that just contain column headings."""
    for record in reversed(records):
        if record.is_heading:
            records.remove(record)


def identify_record(record: Record, task_types: dict):
    """Find the matching task type for a single record."""
    task_type: dict
    for task_type in task_types:
        seconds_min = int(task_type.get('seconds_min', 0))
        if record.seconds < seconds_min:
            continue

        after = _seconds_in_hhmm(int(task_type.get('after', 0)))
        seconds_since_midnight = _seconds_since_midnight(record.start)
        if seconds_since_midnight < after:
            continue

        before = _seconds_in_hhmm(int(task_type.get('before', 2400)))
        if before < seconds_since_midnight + record.seconds:
            continue

        regex = task_type.get('regex', '')
        found = re.search(regex, record.title)
        if not found:
            continue

        name: str = task_type.get('name', _UNKNOWN_TASK_NAME)
        if _GROUP1 in name and len(found.groups()) >= 1:
            name = name.replace(_GROUP1, found[1])
        record.textout = name

        action: str = task_type.get('action', _DEFAULT_ACTION)
        record.action = action
        return
    record.textout = _UNKNOWN_TASK_NAME
    record.action = _DEFAULT_ACTION


def _seconds_in_hhmm(hhmm) -> int:
    """Convert an integer (HHMM) into seconds since midnight."""
    hhmm_hours = int(hhmm / 100)
    hhmm_minutes = int(hhmm % 100)
    total_seconds = 3600 * hhmm_hours + 60 * hhmm_minutes
    return total_seconds


def _seconds_since_midnight(timestamp: datetime) -> int:
    """Convert a timestamp into the number of seconds since the start of the day."""
    midnight = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    return (timestamp - midnight).total_seconds()


def group_records(records: list[Record]) -> list[TimeEntry]:
    """Identify tasks as groups of related records."""
    time_entries: list[TimeEntry] = []
    index = 0
    prev_stop = records[0].start
    while index < len(records):
        record = records[index]

        gap_record = _create_time_gap_record(prev_stop, record)
        if gap_record is not None:
            time_entry = TimeEntry(index, gap_record)
            time_entries.append(time_entry)

        time_entry = TimeEntry(index, record)
        index = time_entry.find_next_index(records)
        time_entries.append(time_entry)
        prev_stop = time_entry.stop
    return time_entries


def _create_time_gap_record(prev_stop: datetime, record: Record):
    """Check if there is a gap between records with unrecorded activity."""
    next_start = record.start
    if prev_stop.date() != next_start.date():
        return None
    gap_seconds = (next_start - prev_stop).total_seconds()
    if abs(gap_seconds) <= MAX_GAP_SECONDS:
        return None
    return Record(prev_stop, gap_seconds, 'Unrecorded Time',
                  action='remove', textout='(Unrecorded Time)')


def report(command: str, entries: list[TimeEntry]):
    """Create a report of the analyzed activity log."""
    cmd = command.lower()
    if cmd.startswith(('col', 'tab')):
        report_timecards(entries)
    elif cmd.startswith(('list', 'task')):
        report_time_entries(entries)
    else:
        print(f'ERROR: Unsupported command "{command}"', file=sys.stderr)


def report_timecards(entries: list[TimeEntry]):
    """Create a report of the time by type in a table."""
    timecard, removed = _project_times_by_day(entries)
    name_width = _get_widest_name(entries)
    _print_table(timecard, name_width)
    _print_table(removed, name_width)


def _project_times_by_day(entries: list[TimeEntry]):
    """Group time entries by name on a weekday."""
    timecard = {}  # dict(entry.name: [entry.seconds])
    removed = {}  # dict(entry.name: [entry.seconds])
    for entry in entries:
        name = entry.name
        weekday = entry.weekday
        seconds = entry.seconds
        if entry.is_paid_hours:
            if name not in timecard:
                timecard[name] = [0, 0, 0, 0, 0, 0, 0]
            timecard[name][weekday] += seconds
        else:
            if name not in removed:
                removed[name] = [0, 0, 0, 0, 0, 0, 0]
            removed[name][weekday] += seconds
    return timecard, removed


def _print_table(timecard: dict, name_width: int):
    """Print a timecard with totals. Rows are projects, columns are weekdays."""
    name_width = max(name_width, len(_NAME_COLUMN_TITLE))
    name_width = min(name_width, _MAX_NAME_COLUMN_WIDTH)
    name_divider = '-' * (name_width)
    print(f'--{name_divider}--------------------------------------------')
    name_column_heading = _NAME_COLUMN_TITLE.center(name_width)
    print(f'| {name_column_heading} | Mon | Tue | Wed | Thu | Fri | Sat | Sun |')
    print(f'--{name_divider}--------------------------------------------')
    for name, seconds in sorted(timecard.items()):
        entry_name = name[:name_width].ljust(name_width)
        print(f'| {entry_name} |', end='')
        for weekday in range(7):
            if seconds[weekday]:
                hours = seconds[weekday] / 3600
                print(f'{hours:4.1f} |', end='')
            else:
                print('     |', end='')
        print()
    print(f'--{name_divider}--------------------------------------------')
    indent = ' ' * (name_width)
    print(f'  {indent} |', end='')
    for weekday in range(7):
        seconds = sum([hours[weekday] for hours in timecard.values()])
        hours = seconds / 3600
        print(f'{hours:4.1f} |', end='')
    print()
    print(f'  {indent} -------------------------------------------')
    print('\n')


def _get_widest_name(entries: list[TimeEntry]):
    """Determine the widest TimeEntry name."""
    return max(len(entry.name) for entry in entries)


def report_time_entries(entries: list[TimeEntry]):
    """Create a report of the time entries in chronological order."""
    prev_stop = entries[0].start - timedelta(days=1)
    for entry in entries:
        if prev_stop.date() != entry.start.date():
            weekday_name: str = _WEEKDAYS[entry.start.weekday()]
            print(weekday_name.center(_BANNER_WIDTH, '-'))
        print(str(entry))
        prev_stop = entry.stop
    print('-' * _BANNER_WIDTH)
