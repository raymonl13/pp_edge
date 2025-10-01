#!/usr/bin/env python3
import argparse,datetime
from zoneinfo import ZoneInfo
ap=argparse.ArgumentParser()
ap.add_argument("--tz",default="America/Los_Angeles")
ap.add_argument("--day",default="")
ap.add_argument("--default",default="tomorrow")
a=ap.parse_args()
if a.day:
    print(a.day)
else:
    now=datetime.datetime.now(ZoneInfo(a.tz))
    d=now.date() if a.default=="today" else now.date()+datetime.timedelta(days=1)
    print(d.isoformat())
