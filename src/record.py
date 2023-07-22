"""Record data object -- data for a single line in the activity log."""

from datetime import date, datetime, time, timedelta

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
_ACTIVE = 'active'
_HEADER_TEXT = 'Time\tUser_Active\tWindow_Handle\tTitle\tApplication'
_INACTIVE = 'inactive'
_NO_HWND = '--------'
_INVALID_HANDLE = -1


class Record():
    """A record found in the activity log."""

    def __init__(self, active:bool=False, hwnd:int=_INVALID_HANDLE, title:str='', app:str=''):
        self.start : datetime = datetime.now()
        self.active : bool = active
        self.hwnd : int = hwnd
        self.title : str = title
        self.app : str = app
        self.seconds : int = 0
        self.activity : str = ''

    def __str__(self) -> str:
        start, active, hwnd = self._format_raw()
        duration = timedelta(seconds=self.seconds).seconds
        return f'{start}\t{duration}\t{active}\t{hwnd}\t{self.title}\t{self.app}'

    @property
    def active_state(self) -> str:
        """Get a string that represents the active/inactive state of the user"""
        if self.active:
            return _ACTIVE
        else:
            return _INACTIVE

    @property
    def date(self) -> date:
        """Get the calendar day that the record started"""
        return self.start.date()

    @staticmethod
    def header_text() -> str:
        """Get the text to use as a header for the record report"""
        return _HEADER_TEXT

    @property
    def hwnd_is_valid(self):
        """Returns True if the activity's window handle is valid"""
        return self.hwnd != _INVALID_HANDLE

    @property
    def stop(self):
        """Use the duration to get the activity stop time"""
        return self.start + timedelta(seconds=self.seconds)

    @stop.setter
    def stop(self, value:datetime):
        """Set the duration based on the activity stop time"""
        self.seconds = (value - self.start).total_seconds()

    @property
    def time_of_day(self) -> time:
        """Get the time of day that the record started"""
        return self.start.time()

    @property
    def weekday(self) -> int:
        """Get the index for the weekday that the record started

        0 (Monday) through 6 (Sunday)
        """
        return self.start.date().weekday()

    def raw_text(self) -> str:
        """Get a string with the raw input values and no processed data"""
        start, active, hwnd = self._format_raw()
        return f'{start}\t{active}\t{hwnd}\t{self.title}\t{self.app}'

    @staticmethod
    def from_string(string:str):
        """Generate a new record from a string"""
        try:
            start, active, hwnd, title, app = string.strip('\r\n').split('\t')
            hwnd = _INVALID_HANDLE if hwnd == _NO_HWND else int(hwnd, base=16)
            record = Record(active == _ACTIVE, hwnd, title, app)
            record.start = datetime.strptime(start, _DATETIME_FORMAT)
            return record
        except ValueError:
            return None

    def _format_raw(self) -> tuple:
        start = self.start.strftime(_DATETIME_FORMAT)
        active = _ACTIVE if self.active else _INACTIVE
        hwnd = _NO_HWND if self.hwnd == _INVALID_HANDLE else f'{self.hwnd:08X}'
        return start, active, hwnd
