"""Routines to analyze the user activity data"""

from argparse import ArgumentParser
from locale import getpreferredencoding
from pathlib import Path
import sys
import json

from logfile import LogFile
from project import Project
from record import Record
from report import Report
from step import Step

_CONFIG_FILE = 'analysis.json'
_LOG_FOLDER = '.'
_SECONDS_PER_HOUR = 3600

def parse_arguments():
    """Get user-selected options"""
    parser = ArgumentParser()
    parser.description = """Analyze user's activity log"""
    parser.add_argument('-c', '--config',
                        type=str, default=_CONFIG_FILE,
                        help='Analysis configuration JSON file (default=analysis.json)')
    parser.add_argument('-f', '--folder',
                        type=str, default=_LOG_FOLDER,
                        help='Folder path for log files')
    parser.add_argument('-t', '--tagged',
                        action='store_true',
                        help='Show tagged records')
    parser.add_argument('-u', '--untagged',
                        action='store_true',
                        help='Show untagged records')
    parser.add_argument('logfile',
                        nargs='?',
                        help='Specify a log file to process.'
                            ' Set to number to auto-select from list')
    return parser.parse_args()

def main():
    """Analyze the user's activity log"""
    args = parse_arguments()

    # Load the analysis configuration settings
    config = _read_config(args.config)

    # Get the logfile to analyze
    try:
        filename = LogFile.select(args.folder, selected=int(args.logfile))
    except (ValueError, TypeError):
        filename = args.logfile or LogFile.select(args.folder)
    if not filename:
        folder = Path(args.folder).absolute()
        sys.exit(f'\nERROR: No log files found in "{folder}"')

    records:list[Record] = LogFile.read(filename)
    if not records:
        filename = Path(filename).absolute()
        sys.exit(f'\nERROR: "{filename}" contains no time records')
    _analyze_records(records, config)

    projects = _define_projects(config)
    untagged_projects = [prj.name for prj in projects.values()
                         if prj.distribute]
    if args.tagged:
        _print_records('Tagged Records', (rec for rec in records
                       if rec.activity not in untagged_projects))
    if args.untagged:
        _print_records('Untagged Records', (rec for rec in records
                       if rec.activity in untagged_projects))

    _group_records_as_projects(records, projects)
    _distribute_times(projects.values())

    # Print information about non-working and unidentified hours
    nonwork = [prj
               for prj in projects.values()
               if not prj.working or prj.distribute and prj.total_hours]
    Report.print_time_card(nonwork, 'Additional Information', group_rows=2)

    _print_summary_data(records, projects.values())

    # Print time card
    working = [prj
               for prj in projects.values()
               if prj.working and not prj.distribute and prj.total_hours]
    Report.print_time_card(working, 'Projects', records[0].start)

    input('\nPress ENTER to quit\n')

def _analyze_records(records:list[Record], cfg:dict):
    step = Step()
    for step_config in cfg['steps']:
        step.apply(step_config, records)

def _print_records(title:str, records:list[Record]):
    print(f'\n {title}:')
    print('=' * 80)
    for record in sorted(records, key=lambda rec: -rec.seconds):
        print(record)

def _define_projects(cfg:dict) -> dict[str,Project]:
    projects:dict[str,Project] = {}
    for project in cfg['projects']:
        project_name = project['name']
        projects[project_name] = Project(project)
    return projects

def _group_records_as_projects(records:list[Record], projects:dict[str,Project]):
    """Apply record weekday times to projects"""
    for record in records:
        if not record.activity or record.activity not in projects:
            continue
        prj = projects[record.activity]
        prj.add_record(record)

def _distribute_times(projects:list[Project]):
    """Distribute times from unidentified active hours to main projects"""
    distributed_seconds = 0
    src_projects = [prj for prj in projects if prj.distribute]
    for src in src_projects:
        dst_projects = [prj for prj in projects
                        if prj.name in src.distribute]
        dst_sum = sum(prj.total_seconds for prj in dst_projects)
        if dst_sum:
            for dst in dst_projects:
                dst.distribute_seconds(src, dst.total_seconds / dst_sum)
        else:
            for dst in dst_projects:
                dst.distribute_seconds(src, 1 / len(dst_projects))
        distributed_seconds += src.total_seconds

def _read_config(configfile:str) -> dict:
    encoding = getpreferredencoding(do_setlocale=False)
    try:
        with open(configfile, encoding=encoding) as fin:
            config = json.load(fin)
            return config
    except FileNotFoundError:
        sys.exit(f'\nERROR: Cannot open configuration file ({configfile})')
    except json.JSONDecodeError as error:
        with open(configfile, encoding=encoding) as fin:
            lines = fin.readlines()
        print(lines[error.lineno - 1].rstrip())
        print(' ' * (error.colno - 1) + '^')
        sys.exit(f'\nERROR: "{configfile}" (line {error.lineno}): {str(error.msg)}')

def _print_summary_data(records:list[Record], projects:list[Project]):
    """Print summary data about the week's time log"""
    # Tally record sub-totals
    lines = []
    active_seconds = 0
    inactive_seconds = 0
    for record in records:
        if record.active:
            active_seconds += record.seconds
        else:
            inactive_seconds += record.seconds
    record_seconds = active_seconds + inactive_seconds
    hours = record_seconds / _SECONDS_PER_HOUR
    lines.append(f'         Total Recorded Time ={hours:5.1f} hours')
    hours = active_seconds / _SECONDS_PER_HOUR
    lines.append(f'                 Active Time ={hours:5.1f} hours')
    hours = inactive_seconds / _SECONDS_PER_HOUR
    lines.append(f'               Inactive Time ={hours:5.1f} hours')

    # Tally project sub-totals
    tagged_seconds = 0
    distributed_seconds = 0
    for project in projects:
        if project.working:
            if project.distribute:
                distributed_seconds += project.total_seconds
            else:
                tagged_seconds += project.total_seconds
    tagged_seconds -= distributed_seconds
    hours = tagged_seconds / _SECONDS_PER_HOUR
    lines.append(f'     Identified Working Time ={hours:5.1f} hours')
    hours = distributed_seconds / _SECONDS_PER_HOUR
    lines.append(f'   Unidentified Working Time ={hours:5.1f} hours')
    lines.append('')

    # Calculate accuracy scores
    if record_seconds:
        working_percent = 100 * (tagged_seconds + distributed_seconds) / record_seconds
        lines.append(f'   Working hours are {working_percent:3.1f}% of recorded hours')
        if tagged_seconds + distributed_seconds > 0:
            identified_percent = 100 * tagged_seconds / (tagged_seconds + distributed_seconds)
            lines.append(f'Identified hours are {identified_percent:3.1f}% of working hours')

    Report.print_box(lines)


if __name__ == '__main__':
    main()
