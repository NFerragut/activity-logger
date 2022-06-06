"""Data structure for a single time entry."""

from datetime import datetime, timedelta


class TimeEntry():
    """A single time entry"""

    def __init__(self, fields):
        assert len(fields) >= 5
        self.start = datetime.strptime(fields[0], '%Y-%m-%d %H:%M:%S')
        try:
            self.seconds = int(fields[1])
        except ValueError:
            self.seconds = 0
        self.title = fields[2]
        self.executable = fields[3]
        try:
            self.hwnd = int(fields[4])
        except ValueError:
            self.hwnd = -1

    @property
    def is_heading(self) -> bool:
        """Return True if the time entry is a heading."""
        return self.title == 'Title'

    @property
    def is_idle(self) -> bool:
        """Return True if the time entry is for idle time."""
        return self.title == 'IDLE'

    @property
    def stop(self) -> datetime:
        """Return the time stop datetime according to the time entry."""
        stoptime = self.start + timedelta(seconds=self.seconds)
        return stoptime

    def __str__(self) -> str:
        return f'{self.start}\t{self.seconds}\t{self.title}\t{self.executable}\t{self.hwnd}'
