"""Report formatter for activity logger"""

from datetime import datetime, timedelta

from project import Project

_COL_WIDTH_FIRST = 42
_COL_WIDTH_TOTAL = 7
_COL_WIDTH_WEEKDAY = 7
_NUM_OF_WEEKDAYS = 7

class Report():
    """Time card report formatter"""
    _col1_width = _COL_WIDTH_FIRST

    @staticmethod
    def print_box(lines:list[str], *, text_width=0):
        """Print a box around lines of text"""
        if not text_width:
            text_width = max([len(line) for line in lines])
        lines = [line.ljust(text_width) for line in lines]
        lines = [line[:text_width] for line in lines]
        width = text_width + 2
        print()
        print('┌' + '─' * width + '┐')
        for line in lines:
            print(f'│ {line} │')
        print('└' + '─' * width + '┘')

    @staticmethod
    def print_time_card(projects:list[Project], title:str='', first_day:datetime=None, \
                        *, group_rows=0):
        """Print the timecard"""
        print()
        Report._print_top_line()
        if first_day:
            Report._print_dates(first_day)
        if title:
            Report._print_title(title)
        if first_day or title:
            Report._print_middle_line()
        hours = Report._print_projects(projects, group_rows=group_rows)
        Report._print_middle_line()
        Report._print_hours('Totals: ', hours, hide_zeros=False, ljust=False)
        Report._print_bottom_line()

    @staticmethod
    def _print_top_line():
        """Print the top line of the report"""
        Report._print_line('┌', '┬', '┐')

    @staticmethod
    def _print_middle_line():
        """Print the top line of the report"""
        Report._print_line('├', '┼', '┤')

    @staticmethod
    def _print_bottom_line():
        """Print the top line of the report"""
        Report._print_line('└', '┴', '┘')

    @staticmethod
    def _print_line(left:str, middle:str, right:str):
        print(left + '─' * Report._col1_width + middle, end='')
        for _ in range(_NUM_OF_WEEKDAYS):
            print('─' * _COL_WIDTH_WEEKDAY + middle, end='')
        print('─' * _COL_WIDTH_TOTAL + right)

    @staticmethod
    def _print_dates(work_date:datetime):
        """Print the dates for the weekday columns"""
        weekday_index = work_date.weekday()
        if weekday_index:
            work_date -= timedelta(days=weekday_index)
        dates = [work_date + timedelta(days=day)
                 for day in range(_NUM_OF_WEEKDAYS)]
        dates_text = [day.strftime('%m-%d')
                      for day in dates]
        Report._print_row('', dates_text, '')

    @staticmethod
    def _print_title(title:str):
        """Print the weekdays for the weekday columns"""
        weekdays_text = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        Report._print_row(title, weekdays_text, 'Total')

    @staticmethod
    def _print_projects(projects:list[Project], *, group_rows=0) -> list[float]:
        """Print project hours for all projects in the list"""
        hours = [0.0] * _NUM_OF_WEEKDAYS
        for index, project in enumerate(sorted(projects, key=lambda prj: prj.long_name), 1):
            Report._print_hours(project.long_name, project.hours)
            if group_rows and index < len(projects) and index % group_rows == 0:
                Report._print_middle_line()
            hours = [sum(hrs) for hrs in zip(hours, project.hours)]
        return hours

    @staticmethod
    def _print_hours(title:str, hours:list[float], *, hide_zeros=True, ljust=True):
        """Print a row of data showing a title, hours, and a total"""
        hours_text:list[str]
        if hide_zeros:
            hours_text = ['' if hrs == 0.0 else f'{hrs:4.1f} '
                          for hrs in hours]
        else:
            hours_text = [f'{hrs:4.1f} ' for hrs in hours]
        total = sum(hours)
        total_text = f'{total:5.1f}'
        Report._print_row(title, hours_text, total_text, ljust=ljust)

    @staticmethod
    def _print_row(title:str, hours:list[str], total:str, *, ljust=True):
        if ljust:
            title = title.ljust(Report._col1_width)[:Report._col1_width]
        else:
            title = title.rjust(Report._col1_width)
        hours = [hrs.center(_COL_WIDTH_WEEKDAY) for hrs in hours]
        total = total.center(_COL_WIDTH_TOTAL)
        print(f'│{title}│', end='')
        for weekday in range(_NUM_OF_WEEKDAYS):
            print(f'{hours[weekday]}│', end='')
        print(f'{total}│')
