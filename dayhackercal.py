#!/usr/bin/python

import sys
import traceback
import urllib
import vobject
from datetime import timedelta, tzinfo, datetime, date

from localtimezone import Local

### monkeypatch vobject.icalendar.stringToDateTime to handle bogus data more elegantly
vobject.icalendar.stringToDateTime_OLD = vobject.icalendar.stringToDateTime

def new_stringToDateTime(s, tzinfo=None):
    try:
        return vobject.icalendar.stringToDateTime_OLD(s, tzinfo)
    except ValueError, e:
        sys.stderr.write("\nWarning: could not parse datetime %s; using now instead.\n" % repr((s,tzinfo)))
        traceback.print_exc(file=sys.stderr)
        return datetime.now()

vobject.icalendar.stringToDateTime = new_stringToDateTime
### end monkeypatch vobject.icalendar.stringToDateTime



def get_events_for_day(ical_url, day):
    """Read the given iCal feed and return an array of events going on today.
    Each event is represented as a dict with the following keys:
        dtstart: datetime or date that the event starts
        dtend: datetime or date that the event ends
        summary: summary title for the event
        is_all_day: boolean; if true, dtstart is a date object; if false, it's a datetime object.

    Note: this function doesn't properly interpret repeating events; it only
    knows about their first occurrence.  To do so, it would have to
    interpret the RRULE field in iCalendar, which would make this function a
    lot more complex, although maybe there is some lib we could use to query
    for whether a given repeating event occurs on the the day in the "day"
    parameter.
    """

    feedstream = urllib.urlopen(ical_url)
    datetime_today = datetime(day.year,
                              day.month,
                              day.day,
                              tzinfo=Local)
    datetime_today_end = datetime(day.year,
                                  day.month,
                                  day.day,
                                  23,59,59,
                                  tzinfo=Local)

    result = []

    try:

        feed = vobject.readComponents(feedstream)

        for component in feed.next().components():
            if component.name == u'VEVENT':
                dtstart = component.dtstart.value
                dtend = component.dtend.value
                summary = component.summary.value or "(unknown)"
                dt_sortable = dtstart
                is_all_day = False

                #sys.stderr.write(" * %s : %s - %s" % (summary[:40], str(dtstart), str(dtend)))

                if isinstance(dtstart, datetime):
                    if dtend < datetime_today or dtstart > datetime_today_end:
                        #sys.stderr.write(" ... skipped\n")
                        continue

                    dtstart = dtstart.astimezone(Local)
                    dtend = dtend.astimezone(Local)

                elif isinstance(dtstart, date):
                    if dtend < day or dtstart > day:
                        #sys.stderr.write(" ... skipped\n")
                        continue 

                    dt_sortable = datetime(dtstart.year,
                                           dtstart.month,
                                           dtstart.day,
                                           tzinfo=Local)
                    is_all_day = True

                else:
                    raise Exception("Confused: don't know how to handle a VEVENT component whose start date is a %s: %s" % (type(dtstart), component))

                #sys.stderr.write(" ... === TODAY! ===\n")
                result.append( dict(dtstart=dtstart,
                                    dtend=dtend,
                                    dt_sortable=dt_sortable,
                                    summary=summary,
                                    is_all_day=is_all_day) )
    except Exception, e:
        traceback.print_exc(file=sys.stderr)
        result.append( dict(dtstart=day,
                            dtend=day,
                            dt_sortable=day,
                            summary="(Error: %s)" % str(e), 
                            is_all_day=True) )
        

    result.sort(key=lambda x: x["dt_sortable"])

    return result

#     for e in result:
#         if isinstance(e["dtstart"], datetime):
#             print u" * %s to %s: %s" % (str(e["dtstart"].astimezone(Local)),
#                                         str(e["dtend"].astimezone(Local)),
#                                         e["summary"])
#         else:
#             print " * ALL DAY EVENT: %s to %s: %s" % (str(e["dtstart"]),
#                                                    str(e["dtend"]),
#                                                    e["summary"])
