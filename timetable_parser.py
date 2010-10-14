#!/usr/bin/env python
import optparse
import sys
from datetime import datetime, date, time, timedelta


optionparser = optparse.OptionParser(usage='%prog inputfile.html')


if __name__ == '__main__':
    options, args = optionparser.parse_args(sys.argv[1:])

    if len(args) < 1:
        optionparser.error('not enough arguments')

    inputfile = open(args[0], 'r')

    import yttp
    parser = yttp.Parser({'au': date(2010, 10, 11), 'sp': date(2011, 01, 10), 'su': date(2011, 04, 26)})
    generator = yttp.Generator()
    sys.stdout.write(generator.generate(parser.parse(inputfile.read())))
