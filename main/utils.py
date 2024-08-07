from main.models import Surfer, SurfSession, SurfSpot, Wave, WavePoint
from datetime import datetime, timedelta, time
from random import randrange


def populate_with_random_surf_sessions():
    maria = Surfer.objects.get(id=2)
    pescadores = SurfSpot.objects.get(id=1)
    create_random_surf_session(maria, pescadores)


def create_random_surf_session(surfer: Surfer, location: SurfSpot):
    session = SurfSession.objects.create(
        name=f"Surfada {location.name}",
        surfer=surfer,
        location=location,
        strava_activity_id="33123",
        duration=time(hour=randrange(0, 1), minute=randrange(30, 59)),
        max_speed=randrange(10, 22),
        number_of_waves=randrange(0, 6),
        date=datetime.now() - timedelta(days=randrange(1, 7))
    )
    wave1_time = session.date + timedelta(minutes=randrange(0, 15))
    wave1 = Wave.objects.create(
        session=session,
        max_speed=randrange(7, 22),
        duration=wave1_time
    )

    WavePoint.objects.create(
        wave=wave1,
        latitude="40.9971720000000000",
        longitude="-8.6490110000000000",
        time=wave1_time
    )
    WavePoint.objects.create(
        wave=wave1,
        latitude="40.9971720000000000",
        longitude="-8.6489680000000000",
        time=wave1_time + timedelta(seconds=1)
    )
    WavePoint.objects.create(
        wave=wave1,
        latitude="40.9971720000000000",
        longitude="-8.6489140000000000",
        time=wave1_time + timedelta(seconds=2)
    )