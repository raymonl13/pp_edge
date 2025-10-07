#!/usr/bin/env python3
from datetime import datetime, timedelta, UTC
import sys
arg=sys.argv[1].strip() if len(sys.argv)>1 else ""
if arg:
    print(arg)
else:
    print((datetime.now(UTC)+timedelta(days=1)).date().isoformat())
