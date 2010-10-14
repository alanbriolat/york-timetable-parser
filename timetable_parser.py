import optparse
import sys
from datetime import datetime, date, time, timedelta

from BeautifulSoup import BeautifulSoup

BLOCK_DURATION = timedelta(minutes=15)
DAY_START = time(hour=9, minute=15)
TYPES = {'L': 'Lecture',
         'S': 'Seminar',
         'P': 'Practical'}
WEEKS = [str(i) + t for t in ('au', 'sp', 'su') for i in xrange(1, 11)]

TERM_DATES = {'au': date(2010, 10, 11),
              'sp': date(2011, 01, 10),
              'su': date(2011, 04, 26)}

WEEK_DATES = dict((w, TERM_DATES[w[-2:]] + timedelta(weeks=int(w[:-2])-1)) for w in WEEKS)


optionparser = optparse.OptionParser(usage='%prog inputfile.html')


def find_day_tables(soup):
    """Get table for each day from document."""
    # Top-level tables alternate between header and data
    return soup.body.findAll('table', recursive=False)[1::2]


def find_day_rows(day_table):
    """Get rows that have timetable data on them."""
    return day_table.tbody.findAll('tr', recursive=False)[1:]


def find_row_events(day_row):
    events = []
    offset = 0
    for block in day_row.findAll('td', bgcolor=lambda value: value is None, recursive=False):
        try:
            length = int(block['colspan'])
            events.append((offset * BLOCK_DURATION,
                           length * BLOCK_DURATION,
                           block))
            offset += length
        except KeyError:
            offset += 1
    return events


def process_weeks(weekspec):
    if '-' in weekspec:
        w1, w2 = weekspec.split('-', 1)
        i1 = WEEKS.index(w1)
        i2 = WEEKS.index(w2)
        return WEEKS[i1:i2+1]
    else:
        if weekspec in WEEKS:
            return [weekspec]
        else:
            raise ValueError('Not a valid week: ' + weekspec)


def process_event(day, offset, length, block):
    event = dict()
    event['day'] = day
    event['offset'] = offset
    event['length'] = length

    row1, row2, row3 = block.findAll('table', recursive=False)
    event['id'] = row1('td')[0].font.string
    event['location'] = row1('td')[1].font.string
    event['type'] = TYPES[event['id'][7]]
    description = row2.font.string
    if ' - ' in description:
        event['desc'], event['desc2'] = description.split(' - ', 1)
    else:
        event['desc'] = description
        event['desc2'] = ''
    event['weeks'] = process_weeks(row3('td')[0].font.string)
    event['staff'] = row3('td')[1].font.string

    start = datetime.combine(WEEK_DATES[event['weeks'][0]], DAY_START) + event['offset']
    end = start + event['length']
    print start, end

    return event


if __name__ == '__main__':
    options, args = optionparser.parse_args(sys.argv[1:])

    if len(args) < 1:
        optionparser.error('No input file specified')

    inputfile = open(args[0], 'r')
    soup = BeautifulSoup(inputfile.read())

    days = find_day_tables(soup)

    for day, day_table in enumerate(days):
        for row in find_day_rows(day_table):
            row_events = find_row_events(row)
            for e in row_events:
                process_event(day, *e)
