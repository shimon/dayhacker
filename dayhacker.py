#!/usr/bin/python
# -*- coding: utf-8 -*-

from dayhacker_personalization import (YOUR_NAME,
                                       ICAL_FEED_URL,
                                       WEATHER_LOCATION,
                                       CLASSIFICATIONS,
                                       CUSTOM_DAY_REMINDERS)


###########################################################################
import time, sys, os, datetime, math, traceback
from localtimezone import utc, Local
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch

import dayhackercal
import sys

LEFT_EDGE = .75*inch
RIGHT_EDGE = letter[0] - .5*inch
TOP_EDGE = letter[1]-.5*inch
BOTTOM_EDGE = .5*inch
XMIDDLE = (letter[0] - LEFT_EDGE) / 2.0

def format_event_line(e):
    start = "%d:%02d" % (e["dtstart"].hour % 12 or 12,  e["dtstart"].minute)
    end = "%d:%02d" % (e["dtend"].hour % 12 or 12,  e["dtend"].minute)
    
    return "%s-%s: %s" % (start,end,e["summary"][:45])

def add_weather_info(canvas, x,y, weather_location):
    try:
        import pywapi
    except ImportError:
        return None

    try:
        weather_info = pywapi.get_weather_from_google(weather_location)
    except Exception, e:
        return None


    canvas.setFontSize(10)
    canvas.drawString(x,y, u"Weather for %s" % (
            weather_info["forecast_information"]["city"],
            ))
    y -= 12

    canvas.setFontSize(8)
    canvas.drawString(x,y, u"%s: %s, High %s°  Low %s°" % (
            weather_info["forecasts"][0]["day_of_week"],
            weather_info["forecasts"][0]["condition"],
            weather_info["forecasts"][0]["high"],
            weather_info["forecasts"][0]["low"]))
    y -= 10

    try:
        curdtstring = weather_info["forecast_information"]["current_date_time"]
        curdt = datetime.datetime.strptime(curdtstring, "%Y-%m-%d %H:%M:%S +0000")
        curdt = curdt.replace(tzinfo=utc).astimezone(Local)
        nowstring = " (%s)" % curdt.strftime("%a %H:%M")
    except Exception, e:
        traceback.print_exc(file=sys.stderr)
        nowstring = ""

    canvas.drawString(x,y, u"Now%s %s, %s°, %s, %s" % (
            nowstring,
            weather_info["current_conditions"]["condition"],
            weather_info["current_conditions"]["temp_f"],
            weather_info["current_conditions"]["humidity"],
            weather_info["current_conditions"]["wind_condition"],
            ))
    


def generate_dayhacker_page(fileobj, day, person_name):
    p = canvas.Canvas(fileobj, pagesize=letter)
    
    #p.setFillColorRGB(1,0,0) # text color

    p.setFont("Helvetica", 14)
    #p.setFontSize(14)
    p.drawString(LEFT_EDGE, TOP_EDGE - 50, u"%s - dayhacker" % (
               person_name))

    if WEATHER_LOCATION:
        add_weather_info(p, LEFT_EDGE, TOP_EDGE - 68, WEATHER_LOCATION)


    ### begin calendar stuff
    if ICAL_FEED_URL:
        p.setFontSize(10)
        vpos = TOP_EDGE - 120


        ## Custom day reminders
        for remindertitle in [ r["title"] for r in CUSTOM_DAY_REMINDERS if r["period"] == "monthly" and r["point"] == day.weekday() and r["seq"] == int( math.floor((day.day-1)/7.0) ) ]:
            p.drawString(LEFT_EDGE, vpos, u"Reminder: %s" % remindertitle)
            vpos -= 12
        ## end custom day reminders


        todays_events = dayhackercal.get_events_for_day(ICAL_FEED_URL, day)
        todays_events_by_hour = dict()

        for e in todays_events:

            if e["is_all_day"]:
                p.drawString(LEFT_EDGE, vpos, u"Today: %s" % e["summary"])
                vpos -= 12
            else:
                #sys.stderr.write(u"EVENT: %s; hour=%d\n" % (repr(e), e["dtstart"].hour))
                todays_events_by_hour.setdefault(e["dtstart"].hour, []).append(e)
    ### end calendar stuff


    p.setFontSize(28)
    dateline = day.strftime("%a, %d %b %Y").replace(" 0"," ")
    
    p.drawString(LEFT_EDGE, TOP_EDGE - 30, dateline)

    p.setFontSize(24)
    p.drawString(XMIDDLE+.5*inch, TOP_EDGE - 25, u"Most Important Things")

    p.setFontSize(20)
    vpos = TOP_EDGE - 60
    for mitnum in range(1,4):
        p.drawString(XMIDDLE+.5*inch, vpos, "%d. _____________________" % mitnum)
        p.rect(RIGHT_EDGE-.28*inch, vpos, .2*inch, .2*inch)
        vpos -= 40


    p.setStrokeColorRGB(0.6,0.6,0.6)
    p.setLineWidth(0.7)
    #p.line(XMIDDLE, TOP_EDGE, XMIDDLE, vpos+.5*inch)
    #p.line(LEFT_EDGE, vpos, RIGHT_EDGE, vpos)


    # Activity Log
    p.setFontSize(24)
    vpos -= 10
    p.drawString(LEFT_EDGE, vpos, "        Activity Log")

    vpos -= 8

    vpos_activity_log_top = vpos
    vpos_activity_log_bottom = vpos

    p.setLineWidth(0.7)
    p.setStrokeColorRGB(0.6,0.6,0.6)

    p.line(LEFT_EDGE, vpos, RIGHT_EDGE, vpos)


    for hour in range(7,22):
        vpos -= 26

        if hour < 12:
            hourstring = "%d" % hour
            ampm = "a"
        elif hour == 12:
            hourstring = "12"
            ampm = "p"
        else:
            hourstring = "%d" % (hour % 12)
            ampm = "p"

        if len(hourstring) == 1:
            hourstring = "  " + hourstring
        p.setFontSize(24)
        p.drawString(LEFT_EDGE, vpos, hourstring)
        p.setFontSize(12)
        p.drawString(LEFT_EDGE+28, vpos+10, ampm)


        ### begin calendar stuff
        if ICAL_FEED_URL:
            p.setFontSize(8)
            eventvpos = vpos + 16
            for eventline in [ format_event_line(e) for e in todays_events_by_hour.get(hour, []) ]:
                p.drawString(LEFT_EDGE+44, eventvpos, eventline)
                eventvpos -= 9
        ### end calendar stuff
        

        vpos -= 7

        p.line(LEFT_EDGE, vpos, RIGHT_EDGE, vpos)

    # now the totals line
    vpos -= 26
    p.setFontSize(24)
    p.drawString(LEFT_EDGE, vpos, "                TOTAL:")
    vpos -= 7
    p.line(LEFT_EDGE, vpos, RIGHT_EDGE, vpos)
    vpos_activity_log_bottom = vpos

    # now draw vert lines for scoring, right to left
    hpos = RIGHT_EDGE
    clns_rev = list(CLASSIFICATIONS)
    clns_rev.reverse()

    for cln in clns_rev:
        p.setFontSize(8)
        p.drawString(hpos + .05*inch - .75*inch, 
                     vpos_activity_log_top + 26, 
                     cln["title1"])
        if "title2" in cln:
            p.drawString(hpos + .05*inch - .75*inch, 
                         vpos_activity_log_top + 18, 
                         cln["title2"])

        p.setFontSize(14)
        p.drawString(hpos + .1*inch - .75*inch, 
                     vpos_activity_log_top + .05*inch,
                     str(cln["score"]))

        p.line(hpos, vpos_activity_log_top + (26+7), hpos, vpos_activity_log_bottom)
        hpos -= .75*inch

    # one more line
    p.line(hpos, vpos_activity_log_top + (26+7), hpos, vpos_activity_log_bottom)
    hpos -= .75*inch

    # a nice BLACK total box 
    p.setStrokeColorRGB(0,0,0)
    p.setLineWidth(1.5)
    p.rect(hpos, vpos_activity_log_bottom, .75*inch, 26+7- (1.5-0.7))

    
    p.showPage()
    p.save()

    return p







if __name__ == "__main__":
    for_date = datetime.date.today()

    if len(sys.argv) >= 2:
        try:
            dayoffset = int(sys.argv[1])
        except ValueError:
            sys.stderr.write("Cannot parse day offset %s; integer required.\n" % repr(sys.argv[1]))
            sys.exit(1)

        for_date += datetime.timedelta(days=dayoffset)

    generate_dayhacker_page(sys.stdout, for_date, YOUR_NAME)
    sys.exit(0)
