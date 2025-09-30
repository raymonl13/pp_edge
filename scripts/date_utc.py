from datetime import datetime, timedelta, timezone
import sys
off = int(sys.argv[1]) if len(sys.argv)>1 else 0
print((datetime.now(timezone.utc)+timedelta(days=off)).strftime('%Y-%m-%d'))
