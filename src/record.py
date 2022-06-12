"""Record data object -- contains a single line from the activity log."""

from datetime import datetime, timedelta

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class Record():
    """A record found in the activity log."""

    def __init__(self, line):
        fields = line.split('\t')
        fields.extend(['', '', '', ''])
        self.start = datetime.strptime(fields[0], _DATETIME_FORMAT)
        try:
            self.seconds = int(fields[1])
        except ValueError:
            self.seconds = 0
        self.title = fields[2]
        self.app = fields[3]
        self.hwnd = fields[4]
        self.action = ''
        self.textout = ''

    @property
    def is_heading(self) -> bool:
        """Return True if record is a heading."""
        return self.title == 'Title'

    @property
    def is_idle(self) -> bool:
        """Return True if record is for idle time."""
        return self.title.startswith('IDLE')

    @property
    def stop(self) -> datetime:
        """Return the datetime that the record ends."""
        return self.start + timedelta(seconds=self.seconds)
