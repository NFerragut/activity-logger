"""Task class -- groups multiple activity log entries as a single task."""

from record import Record

_MAX_LOST_SECONDS = 3
_MAX_TASK_SECONDS = 9000


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
        return f'{timestamp} {seconds:5}   {self._record.textout}'

    def find_next_index(self, records) -> int:
        """Identify the first index that is part of the next task."""
        first_rec: Record = self._record
        curr_rec: Record = first_rec
        for index in range(self.index + 1, len(records)):
            prev_rec: Record = curr_rec
            curr_rec = records[index]

            if curr_rec.is_heading:
                continue

            gap_seconds = (curr_rec.start - prev_rec.stop).total_seconds()
            if abs(gap_seconds) > _MAX_LOST_SECONDS:
                break

            if first_rec.action == 'collapse':
                task_seconds = (curr_rec.stop - first_rec.start).total_seconds()
                if task_seconds > _MAX_TASK_SECONDS:
                    break
                if curr_rec.textout == first_rec.textout:
                    self.seconds = task_seconds
                    self.next_index = index + 1

            else:   # if first_rec.action == 'sequential':
                if curr_rec.textout != first_rec.textout:
                    break
                self.seconds = (curr_rec.stop - first_rec.start).total_seconds()
                self.next_index = index + 1

        return self.next_index
