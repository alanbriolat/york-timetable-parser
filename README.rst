===================================
University of York Timetable Parser
===================================

**This project is redundant - the University of York now provides personalised iCalendar feeds.
I am also no longer a student, and therefore not in a position to continue maintaining or have any
use for this project.**

This is a parser for the personalised timetables supplied by the University of York e:Vision system.  
Converts a saved HTML file to iCalendar (``.ics``) format, which can then be imported into any other 
calendar application that supports it.

A configuration file, using the JSON syntax, can define abbreviations for module names, term dates, 
etc. - look at the supplied ``config.json`` for guidance.  For basic usage help, run ``./yttp.py 
--help``.

The parser currently recognises 3 types of events: lectures, seminars and practicals.  The 
``--split`` option can be used to write a separate calendar for each type of event.

**I take no responsibility if this gets your timetable wrong!  The timetable HTML is horrible and 
there is much room for misinterpretation to happen.  Please take the time to at least do a quick 
check to make sure your timetable is correct.**  (Also, please let me know if your timetable comes 
out incorrect so I can fix it.)

Dependencies:
-------------

* Python 2.6
* The following Python modules:
    
  * icalendar
  * beautifulsoup
  * pytz

License
-------

This software is supplied under the MIT license (see LICENSE).

Credits
-------

Original code by Alan Briolat.  Contributions by

* `Hayashi <http://github.com/CaptainHayashi>`_
* `BRMatt <https://github.com/BRMatt>`_
