from datetime import datetime, time, date, timedelta

from BeautifulSoup import BeautifulSoup


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


class Parser:
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
        for event in self.generate_raw_events(BeautifulSoup(html)):
            event['description'] = self.abbreviations.get(event['description'], event['description'])
            for week in event['weeks']:
                start = datetime.combine(self.date_from_day(week, event['day_of_week']),
                                         self.day_start)
                start += event['offset_blocks'] * self.block_duration
                end = start + event['length_blocks'] * self.block_duration
                yield (start, end, event)

    @staticmethod
    def generate_raw_events(soup):
        """Generate events from parsed HTML."""
        # Every other table is a data table (the rest are day headers)
        for day, day_table in enumerate(soup.body.findAll('table', recursive=False)[1::2]):
            # The first row of a table is the times
            for row in day_table.tbody.findAll('tr', recursive=False)[1:]:
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
        event = dict()
        row1, row2, row3 = event_td.findAll('table', recursive=False)
        event['id'] = row1('td')[0].font.string
        event['location'] = row1('td')[1].font.string
        event['type'] = TYPES[event['id'][7]]
        description = row2.font.string
        if ' - ' in description:
            event['description'], event['description_extra'] = description.split(' - ', 1)
        else:
            event['description'] = description
            event['description_extra'] = ''
        event['weeks'] = Parser.parse_weeks(row3('td')[0].font.string)
        event['staff'] = (row3('td')[1].font.string or '').split(';')
        return event

    @staticmethod
    def parse_weeks(weeks):
        if '-' in weeks:
            w1, w2 = weeks.split('-', 1)
            return WEEKS[WEEKS.index(w1):WEEKS.index(w2)+1]
        else:
            return [weeks]
