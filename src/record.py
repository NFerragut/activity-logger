"""Record data object -- contains a single line from the activity log."""

from datetime import datetime, timedelta


class Record():
    """A record found in the activity log."""

    def __init__(self, /, start=None, seconds=0, title='', *,
                 app='', hwnd=-1, action='', textout=''):
        self.start: datetime = start
        try:
            self.seconds: int = int(seconds)
        except ValueError:
            self.seconds = 0
        self.title: str = str(title)
        self.app: str = str(app)
        self.hwnd: int = hwnd
        self.action: str = str(action)
        self.textout: str = str(textout)

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
