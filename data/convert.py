"""Convert old format activity tracker files into the new format"""

from glob import glob
import re

from record import Record, HEADER_TEXT

def main():
    """Convert all *.tab files found from old format to new format"""
    files = glob('FERRANJ-*.tab')
    for file in files:
        found = re.search(r'\d\d\d\d-\d\d-\d\d', file)
        if not found:
            print(f'Cannot determine week for file "{file}" -- Skipped')
            continue
        week = found[0]

        records = []
        with open(file, 'rt') as fin:
            for line in fin:
                record = Record.from_old_string(line)
                if record:
                    records.append(record)
        for rec_prev, rec_next in zip(records, records[1:]):
            if not rec_next.active and not rec_next.title == HEADER_TEXT:
                rec_next.hwnd: int = rec_prev.hwnd
                rec_next.title: str = rec_prev.title
                rec_next.app: str = rec_prev.app

        with open(f'nelson-{week}.tab', 'wt') as fout:
            for record in records:
                if record.title == HEADER_TEXT:
                    fout.write(HEADER_TEXT)
                else:
                    fout.write(record.raw_text())
                fout.write('\n')

if __name__ == '__main__':
    main()
