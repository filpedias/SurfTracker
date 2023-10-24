import requests
import os
from datetime import datetime

dt_now = datetime.now()

LOG_PATH = "logs"
day = f"{dt_now.year}{dt_now.month}{dt_now.day}"
file_name = f"{day} STRAVA.txt"
file_path = os.path.join(LOG_PATH, file_name)

req = requests.get('http://localhost:8000/api/i/gpx/scan/')


if not os.path.exists(file_path):
    permission = 'w'
else:
    permission = 'a'

with open(file_path, permission) as f:
    f.write(f"{dt_now.strftime('%Y-%m-%d %H:%M:%S')} |  {req.status_code} - {req.text}\n")

from main.strava import update_strava
update_strava()