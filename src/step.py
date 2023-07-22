"""Analysis of the user's activity log"""

from datetime import date, datetime, time, timedelta
import re
import sys

from record import Record

class Activity():
    """Represents an activity as a group of records"""
    def __init__(self, first=-1, first_record=None):
        self.first_index = first
        self.first_record:Record = first_record
        self.last_index = -1
        self.last_record:Record = None

    @property
    def date(self) -> date:
        """Get the calendar day that the activity started"""
        return self.first_record.date

    @property
    def duration(self) -> timedelta:
        """Get the duration of the activity"""
        return self.last_record.stop - self.first_record.start

    @property
    def is_valid(self) -> bool:
        """Verify that both the first and last records are identified"""
        return self.first_index >= 0 and self.first_record and\
                self.last_index >= 0 and self.last_record

class Step():
    """Represents an analysis step applied to a list of records"""
    def __init__(self):
        self.activities:list[Activity] = []
        self.records = []
        self.step = {}
        self.stop_search = False

    def apply(self, step:dict, records:list[Record]):
        """Update the records based on the step criteria."""
        self.step = step
        self.records = records
        self.activities = []
        self._find_step_activities()
        if self.activities:
            self._collapse_records()

    def _find_step_activities(self):
        """Find all activities in the list of records"""
        index = 0
        while index < len(self.records):
            activity = self._find_first_record(index)
            if not activity:
                break
            self._find_last_record(activity)
            if activity.is_valid:
                self.activities.append(activity)
                index = activity.last_index + 1
            else:
                index += 1

    def _find_first_record(self, index) -> Activity:
        """Find the first record that satisfies the first_rule criteria"""
        while index < len(self.records):
            record = self.records[index]
            if self._match_first_rule(record):
                return Activity(index, record)
            index += 1
        return None

    def _match_first_rule(self, record:Record) -> bool:
        first_rule = self.step['first']
        if not _match_record(record, first_rule):
            return False
        if started_at := first_rule.get('started_at', {}):
            if not _in_tod_window(record.time_of_day, started_at):
                return False
        return True

    def _find_last_record(self, activity:Activity):
        """Find the last record that satisfies the last_rule criteria"""
        index = activity.first_index
        self.stop_search = False
        while index < len(self.records):
            record = self.records[index]
            if self._match_last_rule(record, activity):
                activity.last_index = index
                activity.last_record = record
            if self.stop_search:
                break
            index += 1

    def _match_last_rule(self, record:Record, activity:Activity) -> bool:
        last_rule = self.step['last']

        # Check conditions that will stop the search if they are not satisfied
        matched = record.date == activity.date

        if matched and (duration := last_rule.get('duration', {})):
            matched = self._check_duration(duration, activity, record)

        if matched and (continuous := last_rule.get('continuous', [])):
            matched = self._match_continuous(continuous, record)

        if not matched:
            self.stop_search = True
            return False

        # Check conditions that will not stop the search
        matched = _match_record(record, last_rule)

        if matched and (intermittent := last_rule.get('intermittent', str)):
            if intermittent == 'exact_title':
                matched = activity.first_record.title == record.title

        return matched

    def _match_continuous(self, config:str, record:Record) -> bool:
        first_rule = self.step['first']
        matched = True
        if isinstance(config, bool) and config:
            matched = _match_record(record, first_rule)
        elif isinstance(config, list):
            matched = _match_record(record, first_rule, config)
        if not matched:
            self.stop_search = True
        return matched

    def _check_duration(self, config:dict, activity:Activity, record:Record) -> bool:
        duration = record.stop - activity.first_record.start
        too_short, too_long = _in_duration_window(duration, config)
        if too_long:
            self.stop_search = True
        if too_short or too_long:
            return False
        return True

    def _collapse_records(self):
        """Update the list of records based on the previous analysis

        Collapses groups of records that represent an activity into a single
        record in the list."""
        self._check_one_per_day()

        for activity in reversed(self.activities):
            activity.first_record.stop = activity.last_record.stop
            activity.first_record.activity = self.step['activity']
            del self.records[activity.first_index + 1:activity.last_index + 1]

    def _check_one_per_day(self):
        if 'one_per_day' not in self.step:
            return
        index = 0
        while index + 1 < len(self.activities):
            prev_activity = self.activities[index]
            next_activity = self.activities[index + 1]
            if prev_activity.date == next_activity.date:
                self._remove_activity_by_duration(index, self.step['one_per_day'])
            else:
                index += 1

    def _remove_activity_by_duration(self, index:int, method:str):
        dur1 = self.activities[index].duration
        dur2 = self.activities[index + 1].duration
        remove_index:int
        if method == 'shortest':
            remove_index = index if dur1 > dur2 else index + 1
        elif method == 'longest':
            remove_index = index if dur1 < dur2 else index + 1
        del self.activities[remove_index]

def _match_record(record:Record, rule:dict, crit_filter:list[str]=None) -> bool:
    if not crit_filter or 'tagged' not in crit_filter:
        tagged = rule.get('tagged', False)
        if isinstance(tagged, bool):
            if bool(record.activity) != tagged:
                return False
        elif isinstance(tagged, str):
            if record.activity != tagged:
                return False
    for criteria in rule:
        if crit_filter and criteria not in crit_filter:
            continue
        match criteria:
            case 'active':
                if record.active != rule[criteria]:
                    return False
            case 'app':
                if not re.search(rule[criteria], record.app, flags=re.IGNORECASE):
                    return False
            case 'title':
                re_crits = rule[criteria]
                if isinstance(re_crits, str):
                    re_crits = [re_crits]
                if all(not re.search(re_str, record.title, flags=re.IGNORECASE)
                       for re_str in re_crits):
                    return False
    return True

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

def _get_duration(duration_text:str) -> timedelta:
    if found := re.fullmatch(r'(\d\d):(\d\d)', duration_text):
        return timedelta(seconds=3600 * int(found[1]) + 60 * int(found[2]))
    print(f'WARNING: Invalid duration format ("{duration_text}")', file=sys.stderr)
    return timedelta()

def _in_tod_window(time_of_day:time, window:dict) -> bool:
    min_tod = datetime.strptime(window.get('min', '00:00'), '%H:%M').time()
    max_tod = datetime.strptime(window.get('max', '23:59'), '%H:%M').time()
    return min_tod <= time_of_day <= max_tod
