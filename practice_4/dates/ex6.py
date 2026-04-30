from datetime import datetime
import zoneinfo

dt = datetime.now(zoneinfo.ZoneInfo("Asia/Almaty"))
print(dt)