"""Analysis of the user's activity log"""

from datetime import datetime, timedelta
import re
import sys
from re import Match

from record import Record

class Analysis():
    """Perform an analysis of the user's activity log

    Start with all the records from the activity log.
    As the analysis proceeds, replace the Record objects with Entry objects.
    """

    def __init__(self, records:list):
        self.records : list = records.copy()
        self._index = 0
        self._first : int = 0
        self._last : int = 0
        self._prev_record : Record = None

    def do_step(self, step):
        """Scan the activity log for records that satisfy the step criteria.

        Apply the specified step changes to the activity log.
        """
        prev_index = 0
        while prev_index < len(self.records):
            first_index = self.find_first(step['first'], prev_index)
            prev_index = first_index + 1 if first_index >= 0 else prev_index + 1
            last_index = self.find_last(step['last'], first_index)
            if last_index >= 0:
                self.join_records(first_index, last_index, activity=step['activity'])
                self._prev_record = self.records[first_index]
                print(f'{self._prev_record.start}  {self._prev_record.activity}:{self._prev_record.seconds}s')

    def find_first(self, first:dict, index=0) -> int:
        """Find the first record that satisfies the 'first' criteria"""
        while index < len(self.records):
            record = self.records[index]
            if self._match_first(record, first):
                return index
            index += 1
        return -1

    def _match_first(self, record:Record, first:dict) -> bool:
        matched = True
        for criteria in first:
            match criteria:
                case 'active':
                    matched = record.active == first[criteria]
                case 'started_at':
                    matched = _in_tod_window(record.time_of_day, first[criteria])
                case 'once_per_day':
                    if first[criteria] and self._prev_record:
                        matched = self._prev_record.start.date() != record.start.date()
            if not matched:
                return False
        return True

    def find_last(self, last:dict, first_index:int) -> int:
        """Find the last record that satisfies the 'last' criteria"""
        if not 0 <= first_index < len(self.records):
            return first_index            # First record was not found
        first_record = self.records[first_index]

        last_index = -1
        index = first_index
        while index < len(self.records):
            record = self.records[index]
            can_be_last, stop_search = _match_last(first_record, record, last)
            if can_be_last:
                last_index = index
            if stop_search:
                break
            index += 1

        return last_index

    def join_records(self, first:int, last:int, activity=''):
        """Combine records as a single record that represents the activity"""
        record = self.records[first]
        record.activity = activity
        if first < last:
            record.stop = self.records[last].stop
            self.records[first:last + 1] = [record]

def _get_duration(duration_text:str) -> timedelta:
    if found := re.fullmatch(r'(\d\d):(\d\d)', duration_text):
        return timedelta(seconds=3600 * int(found[1]) + 60 * int(found[2]))
    print(f'Invalid duration format ("{duration_text}")', file=sys.stderr)
    return timedelta()

def _in_duration_window(duration:timedelta, window:dict):
    too_short = False
    too_long = False
    if 'min' in window:
        min_duration = _get_duration(window['min'])
        too_short = duration < min_duration
    if 'max' in window:
        max_duration = _get_duration(window['max'])
        too_long = duration > max_duration
    return too_short, too_long

def _in_tod_window(time:datetime, window:dict) -> bool:
    min_tod = datetime.strptime(window.get('min', '00:00'), '%H:%M').time()
    max_tod = datetime.strptime(window.get('max', '24:00'), '%H:%M').time()
    return min_tod <= time <= max_tod

def _match_last(first:Record, record:Record, last:dict) -> tuple[bool, bool]:
    can_be_last = True
    stop_search = False
    for criteria in last:
        match criteria:
            case 'active':
                can_be_last = record.active == last[criteria]
                if not can_be_last:
                    stop_search = True
                    break
            case 'duration':
                duration = record.stop - first.start
                (too_short, too_long) = _in_duration_window(duration, last[criteria])
                if too_short or too_long:
                    can_be_last = False
                if too_long:
                    stop_search = True
                    break
        if stop_search:
            break
    return can_be_last, stop_search
