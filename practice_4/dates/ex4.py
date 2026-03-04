from datetime import datetime
date_string = "2026-02-27 14:30:00"

dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
print(dt)