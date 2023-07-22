"""Project in the user's activity log"""

from record import Record

_NUM_OF_DAYS = 7
_POJECT_COLUMN_WIDTH = 45
_SECONDS_PER_HOUR = 3600

class Project():
    """Information for a single project on the hour log report"""
    proj_col_width = _POJECT_COLUMN_WIDTH

    def __init__(self, project:dict):
        self.distribute:list = project.get('distribute', [])
        self.name:str = project['name']
        self.long_name:str = project['long_name']
        self.working:bool = project['working']
        self.seconds:list = [0.0] * _NUM_OF_DAYS
        self._total:float = 0.0

    @property
    def hours(self) -> list[float]:
        """Get the number of hours assigned to each weekday in this project"""
        return [self._get_weekday_hours(weekday)
                for weekday in range(_NUM_OF_DAYS)]

    @property
    def total_hours(self) -> float:
        """Get the total number of hours assigned to this project"""
        return round(self._total / _SECONDS_PER_HOUR, 1)

    @property
    def total_seconds(self) -> int:
        """Get the total number of seconds assigned to this project"""
        return self._total

    def add_record(self, record:Record):
        """Add the time for a record to this project"""
        self.seconds[record.weekday] += record.seconds
        self._total += record.seconds

    def clear_seconds(self):
        """Reset the time associated with this project"""
        self.seconds = [0.0] * _NUM_OF_DAYS
        self._total = 0.0

    def distribute_seconds(self, src:'Project', ratio:float):
        """Distribute a percentage of all seconds from the src Project."""
        seconds = [ratio * sec for sec in src.seconds]
        self.seconds = [sum(secs) for secs in zip(self.seconds, seconds)]
        self._total += sum(seconds)

    def _get_weekday_hours(self, weekday:int) -> float:
        """Get the number of hours for the given weekday"""
        return round(self.seconds[weekday] / _SECONDS_PER_HOUR, 1)
