"""Task class -- groups multiple activity log entries as a single task."""

from datetime import datetime, timedelta
from record import Record

MAX_GAP_SECONDS = 3
_MAX_COLLAPSE_TIME_ENTRY_SECONDS = 9000


class TimeEntry():
    """Task class groups multiple activity log entries as a single task."""

    def __init__(self, index: int, record: Record):
        assert not record.is_heading
        self._record: Record = record
        self.index: int = index
        self.next_index: int = index + 1
        self.seconds: int = record.seconds

    def __str__(self) -> str:
        timestamp = self._record.start.strftime('%Y-%m-%d %H:%M:%S')
        seconds = int(self.seconds)
        return f'{timestamp}{seconds:6.0f}   {self._record.textout}'

    @property
    def is_paid_hours(self) -> bool:
        """Return True if the time entry is for paid work."""
        return self._record.action != 'remove'

    @property
    def name(self) -> str:
        """Return the name of the time entry."""
        return self._record.textout

    @property
    def start(self) -> datetime:
        """Return the time that the time entry's activity started."""
        return self._record.start

    @property
    def stop(self) -> datetime:
        """Return the time that the time entry's activity ended."""
        return self._record.start + timedelta(seconds=self.seconds)

    @property
    def weekday(self) -> int:
        """Return the weekday that the time entry was started."""
        return self._record.start.weekday()

    def find_next_index(self, records: list[Record]) -> int:
        """Identify the first index of the next time entry."""
        first_rec = self._record
        last_rec = self._record

        record = first_rec
        for index in range(self.index + 1, len(records)):
            stop_time = record.stop
            record = records[index]

            gap_seconds = (record.start - stop_time).total_seconds()
            if abs(gap_seconds) > MAX_GAP_SECONDS:
                # Do not span a time entry across missing data in the activity records.
                break

            if first_rec.action == 'collapse':
                time_entry_seconds = (record.stop - first_rec.start).total_seconds()
                if time_entry_seconds > _MAX_COLLAPSE_TIME_ENTRY_SECONDS:
                    # Do not span a collapse time entry longer than the maximum time.
                    break
                if record.textout == first_rec.textout:
                    last_rec = record

            else:
                if record.textout != first_rec.textout:
                    # Do not span a time entry across records with different names.
                    # (other than those with the 'collapse' action)
                    break
                last_rec = record

        self.seconds = (last_rec.stop - first_rec.start).total_seconds()
        self.next_index = records.index(last_rec) + 1
        return self.next_index
