===================================
University of York Timetable Parser
===================================

This is a parser for the personalised timetables supplied by the University of York e:Vision system.  
Converts a saved HTML file to iCalendar (``.ics``) format, which can then be imported into any other 
calendar application that supports it.

A configuration file, using the JSON syntax, can define abbreviations for module names, term dates, 
etc. - look at the supplied ``config.json`` for guidance.  For basic usage help, run ``./yttp.py 
--help``.

The parser currently recognises 3 types of events: lectures, seminars and practicals.  The 
``--split`` option can be used to write a separate calendar for each type of event.

Dependencies:
-------------

* Python 2.6
* The following Python modules:
  * icalendar
  * beautifulsoup
  * pytz
