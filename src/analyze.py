"""Routines to analyze the user activity data"""

from argparse import ArgumentParser
from locale import getpreferredencoding
from pathlib import Path
import sys
import json

from addict import Dict
from analysis import Analysis
from logfile import LogFile
from record import Record

_CONFIG_FILE = 'analysis.json'
_LOG_FOLDER = '.'

def parse_arguments():
    """Get user-selected options"""
    parser = ArgumentParser()
    parser.description = """Analyze user's activity log"""
    parser.add_argument('-c', '--config',
                        type=str, default=_CONFIG_FILE,
                        help='Analysis configuration JSON file')
    parser.add_argument('-f', '--folder',
                        type=str, default=_LOG_FOLDER,
                        help='Folder path for log files')
    parser.add_argument('logfile',
                        nargs='?',
                        help='Specify a log file to process')
    return parser.parse_args()

def main():
    """Analyze the user's activity log"""
    args = parse_arguments()

    # Load the analysis configuration settings
    cfg = _read_config(args.config)

    # Get the logfile to analyze
    filename = args.logfile or LogFile.select(args.folder)
    if not filename:
        folder = Path(args.folder).absolute()
        sys.exit(f'ERROR: No log files found in "{folder}"')

    # Read all records from the logfile
    records = LogFile.read(filename)

    # Analyze the records
    analysis = Analysis(records)
    analysis.do_step(cfg.steps[0])

def _read_config(configfile:str) -> dict:
    encoding = getpreferredencoding(do_setlocale=False)
    with open(configfile, encoding=encoding) as fin:
        try:
            config = Dict(json.load(fin))
            return config
        except json.JSONDecodeError as error:
            with open(configfile, encoding=encoding) as fin:
                lines = fin.readlines()
            print(lines[error.lineno - 1].rstrip())
            print(' ' * (error.colno - 1) + '^')
            print(f'ERROR: "{configfile}" (line {error.lineno}): {str(error.msg)}')
            sys.exit(-1)

if __name__ == '__main__':
    main()
