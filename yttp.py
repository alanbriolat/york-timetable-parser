#!/usr/bin/env python
import optparse
import sys
import json
from datetime import datetime, time, date, timedelta

from BeautifulSoup import BeautifulSoup
from icalendar import Calendar, Event
import pytz


GMT = pytz.timezone('Europe/London')
UTC = pytz.utc
TERMS = ('au', 'sp', 'su')
WEEKS = [str(i) + t for t in TERMS for i in xrange(1, 11)]
TYPES = {'L': 'Lecture',
         'S': 'Seminar',
         'P': 'Practical'}


def _week_date(term_dates, week):
    """Get the start date for *week* (e.g. 9su) based on *term_dates*."""
    term = week[-2:]
    weeknum = int(week[:-2])
    return term_dates[term] + timedelta(weeks=weeknum-1)


def _correct_datetime(dt):
    return GMT.normalize(GMT.localize(dt)).astimezone(UTC)


class Parser:
    """University of York timetable parser.

    The :class:`Parser` class is responsible for parsing a saved HTML file from
    the e:Vision portal personalised timetable page and turning it into a stream
    of events.

    *term_dates* is a dictionary mapping term abbreviation (``au``, ``sp`` and
    ``su`` for Autumn, Spring and Summer respectively) to :class:`datetime.date`
    objects which represent the date of Monday week 1 for each term.
    """
    def __init__(self, term_dates, abbrev={}, start=None, block=None):
        self.term_dates = term_dates
        self.week_dates = dict(zip(WEEKS, (_week_date(self.term_dates, w)
                                           for w in WEEKS)))
        self.abbreviations = abbrev
        self.day_start = start if start is not None else time(hour=9, minute=15)
        self.block_duration = block if block is not None else timedelta(minutes=15)

    def date_from_day(self, week, day):
        """Given a valid *week* (e.g. 9su) and *day* (0-4) calculate the date."""
        return self.week_dates[week] + timedelta(days=day)

    def parse(self, html):
        """Parse *html* and generate events as ``(start, end, event)`` tuples.

        Each event is a ``(start, end , event)`` tuple, where ``start`` and
        ``end`` are :class:`datetime.datetime` objects representing the start
        and end of the event, and ``event`` is a dictionary containing the
        details of the event.
        """
        for event in self.generate_raw_events(BeautifulSoup(html)):
            event['description'] = self.abbreviations.get(event['description'], event['description'])
            for week in event['weeks']:
                start = datetime.combine(self.date_from_day(week, event['day_of_week']),
                                         self.day_start)
                start += event['offset_blocks'] * self.block_duration
                end = start + event['length_blocks'] * self.block_duration
                start = _correct_datetime(start)
                end = _correct_datetime(end)
                yield (start, end, event)

    @staticmethod
    def generate_raw_events(soup):
        """Generate events from parsed HTML."""
        # Every other table is a data table (the rest are day headers)
        for day, day_table in enumerate(soup.body.findAll('table', recursive=False)[1::2]):
            # Some browsers (Google Chrome) like to "fix" HTML when they save it,
            # and introduce phantom <tbody> tags.  Use this to look for <tr> if 
            # it exists
            if day_table.tbody is not None:
                day_table = day_table.tbody
            # The first row of a table is the times
            for row in day_table.findAll('tr', recursive=False)[1:]:
                offset = 0
                # Only the day name has a background colour
                for event_td in row.findAll('td', bgcolor=lambda value: value is None, recursive=False):
                    # Blocks that aren't events don't have colspan
                    try:
                        length = int(event_td['colspan'])
                        event = Parser.parse_event_td(event_td)
                        event['offset_blocks'] = offset
                        event['length_blocks'] = length
                        event['day_of_week'] = day
                        yield event
                        offset += length
                    except KeyError:
                        offset += 1

    @staticmethod
    def parse_event_td(event_td):
        """Extract event details from *event_td* as a dictionary."""
        event = dict()
        row1, row2, row3 = event_td.findAll('table', recursive=False)
        event['id'] = row1('td')[0].font.string
        event['location'] = row1('td')[1].font.a.string.replace('&amp;', '&')
        event['type'] = Parser.parse_event_type(event['id'])
        description = row2.font.string.replace('&amp;', '&')
        if ' - ' in description:
            event['description'], event['description_extra'] = description.split(' - ', 1)
        else:
            event['description'] = description
            event['description_extra'] = ''
        event['weeks'] = Parser.parse_weeks(row3('td')[0].font.string)
        event['staff'] = (row3('td')[1].font.string or '').split(';')
        return event

    @staticmethod
    def parse_event_type(event_id):
        """Extract event type from ID string."""
        type_key = event_id.split('/', 1)[0].rstrip('0123456789')[-1]
        return TYPES.get(type_key, '(Unknown type)')

    @staticmethod
    def parse_weeks(weeks):
        """Convert a week specification into a list of weeks."""
        allweeks = []
        for weekrange in weeks.split(', '):
            if '-' in weekrange:
                w1, w2 = weekrange.split('-', 1)
                allweeks += WEEKS[WEEKS.index(w1):WEEKS.index(w2)+1]
            else:
                allweeks.append(weekrange)
        return allweeks


class Generator:
    """iCalendar file generator.

    Generates iCalendar files from streams of events.
    """
    def __init__(self, summary_fmt='%(description)s (%(type)s)'):
        self.summary_fmt = summary_fmt

    def generate(self, events, event_filter=None):
        cal = Calendar()
        cal.add('prodid', '-//york-timetable-converter//alanbriolat//EN')
        cal.add('version', '2.0')

        for start, end, event in events:
            if event_filter is not None and not event_filter(event):
                continue
            ev = Event()
            ev.add('summary', self.summary_fmt % event)
            ev.add('location', event['location'])
            ev.add('dtstart', start)
            ev.add('dtend', end)
            ev.add('dtstamp', datetime.utcnow().replace(tzinfo=UTC))
            # The above generates 'DTSTART;VALUE=DATE:...', which Google Calendar
            # doesn't like - this fixes that problem
            ev['dtstart'] = str(ev['dtstart'])
            ev['dtend'] = str(ev['dtend'])
            ev['dtstamp'] = str(ev['dtstamp'])
            ev['uid'] = start.strftime('%Y%m%dT%H%M%SZ/') + event['id'] + '@york.ac.uk'
            cal.add_component(ev)

        return cal.as_string()


def write_separate(generator, events, prefix=''):
    for t in TYPES.values():
        fp = open(prefix + t + '.ics', 'wb')
        fp.write(generator.generate(events, event_filter=lambda e: e['type'] == t))
        fp.close()


if __name__ == '__main__':
    optionparser = optparse.OptionParser(usage='%prog config.json timetable.html')
    optionparser.add_option('-s', '--split',
                            metavar='PREFIX',
                            help='generate one calendar per event type with '
                                 'filenames of <PREFIX><TYPE>.ics')
    optionparser.add_option('-o', '--outfile',
                            metavar='FILE',
                            help='output to FILE instead of stdout')

    options, args = optionparser.parse_args(sys.argv[1:])

    if len(args) < 2:
        optionparser.error('not enough arguments')

    config = json.load(open(args[0], 'r'))
    # Convert year/month/day dates into datetime.date objects
    for k in config['termdates']:
        config['termdates'][k] = date(*(map(int, config['termdates'][k].split('/'))))

    parser = Parser(term_dates=config['termdates'], abbrev=config['abbreviations'])
    generator = Generator(summary_fmt=config['summary_format'])

    events = list(parser.parse(open(args[1], 'r')))

    if options.split is not None:
        write_separate(generator, events, options.split)
    elif options.outfile is not None:
        outfile = open(options.outfile, 'wb')
        outfile.write(generator.generate(events))
        outfile.close()
    else:
        sys.stdout.write(generator.generate(events))
