"""Manage log files"""

from datetime import datetime, timedelta
from locale import getpreferredencoding
from glob import glob
import logging
from os import getlogin, makedirs
import re

from windows_activity import WindowsActivity
from record import Record

_FILE_DATE_FORMAT = '%Y-%m-%d'
_LOG_FOLDER = '.'

class LogFile():
    """Manage log files"""

    @staticmethod
    def prepare(folder:str = _LOG_FOLDER):
        """Configure root logging to generate activity records"""
        makedirs(folder, exist_ok=True)         # ensure log folder exists
        logfile = _get_current_logfile()
        filename = f'{folder}/{logfile}'
        logging.basicConfig(filename=filename,
                            format='%(message)s',
                            level=logging.INFO)

    @staticmethod
    def read(filename:str) -> list:
        """Read the activity records from the specified log file"""
        encoding = getpreferredencoding(do_setlocale=False)
        records = []
        with open(filename, 'rt', encoding=encoding) as fin:
            prev_rec:Record = None
            for line in fin:
                record = Record.from_string(line)
                if record:
                    records.append(record)
                    if prev_rec:
                        prev_rec.stop = record.start
                    prev_rec = record
        return records

    @staticmethod
    def select(folder:str, how_many:int=3) -> str:
        """Prompt the user to select a recent log file from a list"""
        logfiles = _find_all_logfiles(folder)
        if not logfiles:
            return ''
        weeks = _get_recent_weeks(logfiles, how_many)
        selected = None
        while selected not in weeks:
            selected = _get_selected_week(weeks)
        return logfiles[selected]


def _get_current_logfile() -> str:
    """Get the log filename that corresponds to the current week"""
    datestamp = datetime.now()
    startofweek = datestamp - timedelta(days=datestamp.weekday())
    return _get_logfile(startofweek)

def _get_logfile(date:datetime):
    username = getlogin()
    datestamp = date.strftime(_FILE_DATE_FORMAT)
    return f'{username}-{datestamp}.tab'

def _find_all_logfiles(folder:str):
    logfiles = {}
    username = getlogin()
    files = glob(f'{folder}/{username}-*.tab')
    for file in files:
        if found := re.search(username + r'\-(\d{4}\-\d\d\-\d\d)\.tab', file):
            firstday = datetime.strptime(found[1], _FILE_DATE_FORMAT)
            logfiles[firstday] = file
    return logfiles

def _get_recent_weeks(logfiles:dict, how_many:int) -> list:
    weeks = list(logfiles.keys())
    weeks.sort(reverse=True)
    if how_many < len(weeks):
        weeks = weeks[:how_many]
    return weeks

def _get_selected_week(weeks) -> datetime:
    print('\nChoose a log file:')
    for number, week in enumerate(weeks, 1):
        filename = _get_logfile(week)
        print(f'  {number}: {filename}')
    key = ''
    while not key:
        key = WindowsActivity.get_keypress()
    try:
        index = int(key) - 1
        if index in range(len(weeks)):
            return weeks[index]
    except ValueError:
        pass
    return None
