import random
import pytz
from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import time, datetime, timedelta


class Surfer(AbstractUser):
    class Meta:
        verbose_name_plural = "Surfers"

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    strava_user_id = models.CharField(max_length=90)
    strava_code = models.CharField(max_length=90)
    boards = models.ManyToManyField("main.SurfBoard", verbose_name=("surfboards"))

    def __str__(self):
        return f"{self.first_name} {self.last_name} | Strava ID: {self.strava_user_id}"


class SurfSpot(models.Model):
    name = models.CharField("Name", max_length=90, default="")
    latitude = models.DecimalField("Latitude", max_digits=22, decimal_places=16)
    longitude = models.DecimalField("Longitude", max_digits=22, decimal_places=16)
    short_name = models.CharField("Image name", max_length=90, default="")
    is_saved = models.BooleanField("Saved", default=False)
    
    # 40°59'54.4"N 8°38'48.4"W pescadores
    def __str__(self):
        return self.name


class SurfSession(models.Model):
    name = models.CharField("Name", max_length=90, default="")
    surfer = models.ForeignKey(Surfer, on_delete=models.CASCADE)
    location = models.ForeignKey(SurfSpot, on_delete=models.CASCADE, null=True)
    strava_activity_id = models.CharField("Strava Activity", max_length=90)
    number_of_waves = models.IntegerField(default=0)
    duration = models.TimeField("Duration", default=time(0, 0))
    max_speed = models.DecimalField("Speed (km/h)", default=0, max_digits=4, decimal_places=1)
    date = models.DateTimeField(null=True, default=datetime.now() - timedelta(days=random.randrange(1,20)))
    has_gpx_data = models.BooleanField(default=False)

    def display_date(self):
        if not self.date:
            return "-"
        local_tz = pytz.timezone('Europe/Lisbon')
        dt_begin_today = datetime.now(local_tz).replace(hour=0, minute=0)

        dt_begin_yesterday = dt_begin_today - timedelta(days=1)
        
        if self.date > dt_begin_today:
            return f"Today at {self.date.strftime('%H:%M')}"
        elif self.date > dt_begin_yesterday:
            return f"Yesterday at {self.date.strftime('%H:%M')}"
        else:
            return f"{self.date.strftime('%A')} {self.date.strftime('%d %B')} at {self.date.strftime('%H:%M')}"

    def display_duration(self):
        return f"{self.duration.minute}min" if self.duration.hour == 0 else f"{self.duration.hour}h{self.duration.minute}min"

    def display_max_speed(self):
        return f"{self.max_speed} km/h"

    def __str__(self):
        return f"{self.display_date()} | {self.surfer.first_name} @ {self.location.name}"

    def get_session_gpx(self):
        gpx_session_waves = []
        session_waves = Wave.objects.filter(session=self)
        for w in session_waves:
            session_wave_gpx = []
            session_wave = WavePoint.objects.filter(wave=w)
            for wp in session_wave:
                session_wave_gpx.append({
                    "latitude": float(wp.latitude),
                    "longitude": float(wp.longitude),
                    "time": wp.time.strftime('%Y-%m-%d %H:%M:%S'),
                })
                gpx_session_waves.append(session_wave_gpx)
        
        return gpx_session_waves

    def get_json_data(self):
        return {
            "session_id": self.id,
            "name": self.name,
            "spot_lat": float(self.location.latitude),
            "spot_long": float(self.location.longitude),
            "wave_points": self.get_session_gpx()
        }


class Wave(models.Model):
    session = models.ForeignKey(SurfSession, on_delete=models.CASCADE)
    duration = models.TimeField("Duration", default=time(0, 0), null=True)
    max_speed = models.DecimalField("Speed (km/h)", default=0, max_digits=4, decimal_places=1, null=True)

    def __str__(self):
        return f"{self.session} | {self.id}"

class WavePoint(models.Model):
    wave = models.ForeignKey(Wave, on_delete=models.CASCADE)
    latitude = models.DecimalField("Latitude", max_digits=22, decimal_places=16)
    longitude = models.DecimalField("Longitude", max_digits=22, decimal_places=16)
    time = models.DateTimeField("Time", null=True, blank=True)

    def __str__(self):
        return f"{self.wave.session} | {self.wave} | ({self.latitude}, {self.longitude})"
    
class WaveConfigs(models.Model):
    name = models.CharField("Name", max_length=90, default="")
    min_speed_to_start_wave = models.DecimalField("Speed To Trigger Wave Start", default=8, max_digits=4, decimal_places=1)
    min_speed_to_stop_wave = models.DecimalField("Speed To Trigger Wave End", default=8, max_digits=4, decimal_places=1)
    minimum_time_of_event_to_consider_wave = models.DecimalField("Seconds To Consider Wave", default=2.5, max_digits=4, decimal_places=1)
    min_max_speed_during_event_to_consider_wave = models.DecimalField("Min. Max speed on wave", default=11, max_digits=4, decimal_places=1)

    def display_min_speed_to_start_wave(self):
        return f"{self.min_speed_to_start_wave} km/h"

    def display_min_speed_to_stop_wave(self):
        return f"{self.min_speed_to_stop_wave} km/h"

    def display_min_max_speed_during_event_to_consider_wave(self):
        return f"{self.min_max_speed_during_event_to_consider_wave} km/h"

    def __str__(self):
        return f"Speed to start/stop wave: {self.display_min_speed_to_start_wave()} | Seconds to consider wave: {self.minimum_time_of_event_to_consider_wave}s"


class SurfBoard(models.Model):
    name = models.CharField("Name", max_length=90, default="", null=True)
    brand = models.CharField("Brand", max_length=90, default="", null=True)
    model = models.CharField("Model", max_length=90, default="", null=True)
    width = models.CharField("Width", blank=True, max_length=6)
    length = models.CharField("Length", blank=True, max_length=6)
    thickness = models.CharField("Thickness", blank=True, max_length=6)
    volume = models.DecimalField("Volume", blank=True, max_digits=6, decimal_places=2)
    image_name = models.CharField("Image Name", blank=True, max_length=36)
    