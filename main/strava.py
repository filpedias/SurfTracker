"""
File responsible to handle all strava communications 
"""

import json
import os
import requests
import pandas as pd
import gpxpy.gpx
import gpxpy
from datetime import datetime, timedelta, time as dt_time
from time import time, sleep
from urllib3.connection import ConnectionError
from main.settings import TZ_LOCAL
from main.models import Surfer, SurfSession, SurfSpot, Wave, WaveConfigs, WavePoint
from main.configs import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, STRAVA_USER_ID

global access_token
global exceed_counter
global data_folder

exceed_counter = 0
data_folder = 'gpx/'


def request_token(code):
    try:
        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
    except ConnectionError as ce:
        print(ce)

    return response

def refresh_token(refresh_token):
    try:
        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
                
            }
        )
    except ConnectionError as ce:
        print(ce)

    return response


def write_token(tokens):
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)


def get_token():
    with open('strava_tokens.json', 'r') as tokens:
        data = json.load(tokens)

    return data

def update_strava():
    response = {'status': 'ok', "msg": []}
    surfer = Surfer.objects.get(strava_user_id=STRAVA_USER_ID)

    if not os.path.exists('strava_tokens.json'):
        request_url = f'http://www.strava.com/oauth/authorize?client_id={CLIENT_ID}' \
                    f'&response_type=code&redirect_uri={REDIRECT_URI}' \
                    f'&scope=profile:read_all,activity:read_all'

        print('Click here:', request_url)
        print('Please authorize the app and copy&paste below the generated code!')
        print('P.S: you can find the code in the URL')
        code = input('Insert the code from the url: ')

        tokens = request_token(code)

        # Save json response as a variable
        strava_tokens = tokens.json()
        # Save tokens to file
        write_token(strava_tokens)

    data = get_token()

    if data['expires_at'] < time():
        response["msg"].append("Token on strava_tokens expired")
        new_tokens = refresh_token(surfer.strava_code)
        if new_tokens.status_code == 200:
            # Update the file
            write_token(new_tokens)
        else:
            response["msg"].append("Token refresh failed")
            response["status"] = "error"

    data = get_token()

    access_token = data['access_token']

    athlete_url = f"https://www.strava.com/api/v3/athlete?access_token={access_token}"
    try:
        athlete_response = requests.get(athlete_url)
        if athlete_response.status_code == 200:

            activities_url = f"https://www.strava.com/api/v3/athlete/activities"
            activities_response = requests.get(activities_url, headers={
                "accept": "application/json",
                "authorization": f"Bearer {access_token}"
            })
            if activities_response.status_code == 200:
                activities = activities_response.json()
                surfing_activities = []

                for activity in activities:
                    if 'type' in activity and activity['type'] == 'Surfing':
                        surfing_activities.append(activity)
                
                new_sessions_added = []
                if surfer:
                    new_sessions_added = load_surfing_activities_from_strava(
                        surfing_activities, surfer, access_token
                    )
                    response["msg"].append(
                        f"Added {len(new_sessions_added)} new surf sessions "
                    )
            else:
                error_msg = f"{activities_url} returned {athlete_response.status_code}"
                response["msg"].append(error_msg)
                response["status"] = "error"
        else:
            error_msg = f"Athlete activities request returned {athlete_response.status_code}"
            response["msg"].append(error_msg)
            response["status"] = "error"
    except ConnectionError as ce:
        error_msg = f"ConnectionError: {ce}"
        response["msg"].append(error_msg)
        response["status"] = "error"
    return response


def load_surfing_activities_from_strava(activities, surfer, access_token):

    new_surf_activities = []

    surf_sessions = SurfSession.objects.filter(surfer=surfer).values_list(
        'strava_activity_id', flat=True
    )

    for activity in activities:
        if activity['type'] == 'Surfing':
            if str(activity['id']) not in surf_sessions:
                activity_duration = determine_duration(activity)
                if activity_duration > dt_time(0, 20):
                    activity_analysis = get_activity_analysis_data(activity, access_token)
                    if len(activity_analysis.keys()) == 0:
                        continue
                    s = SurfSession()
                    s.surfer = surfer
                    s.date = activity['start_date']
                    s.strava_activity_id = activity['id']
                    s.name = activity['name']
                    s.duration = activity_duration
                    s.location = activity_analysis['location']
                    s.has_gpx_data = activity_analysis['gpx_created']
                    s.number_of_waves = activity_analysis['number_of_waves']
                    s.max_speed = activity_analysis['max_speed']
                    s.save()

                    for wave in activity_analysis['waves_points']:
                        w = Wave()
                        w.session = s
                        w.save()
                        # w.duration = wave['duration']
                        for wave_point in wave:
                            wp = WavePoint()
                            wp.wave = w
                            wp.latitude = wave_point['latitude']
                            wp.longitude = wave_point['longitude']
                            wp.time = datetime.strptime(wave_point['time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZ_LOCAL)
                            wp.save()

                    new_surf_activities.append(s)

    return new_surf_activities


def determine_duration(activity):
    activity_total_seconds = activity["elapsed_time"]
    minutes, seconds = divmod(activity_total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return dt_time(hours, minutes, seconds)


def get_activity_analysis_data(activity, access_token):

    gpx_creation = create_gpx_activity_file(activity, access_token)
    gpx_analysis = analyze_gpx(activity['id'])

    if not gpx_creation['start_coordinates']:
        return {}

    return {
        'location': determine_location(gpx_creation['start_coordinates']),
        'gpx_created': gpx_creation['gpx_created'],
        'number_of_waves': gpx_analysis['number_of_waves'],
        'max_speed': gpx_analysis['max_speed'],
        'waves_speeds': gpx_analysis['waves_speeds'],
        'waves_points': gpx_analysis['waves_points']
    }


def create_gpx_activity_file(activity, access_token):

    strava_id = activity['id']
    start_time = activity['start_date']

    url = f"https://www.strava.com/api/v3/activities/{strava_id}/streams?" \
            f"access_token={access_token}"
    latlong = requests.get(f"{url}&keys=latlng").json()
    time_list = requests.get(f"{url}&keys=time").json()
    altitude = requests.get(f"{url}&keys=altitude").json()
    for r in [latlong, time_list, altitude]:
        if isinstance(r, dict) and 'message' in r.keys():
            check = r['message']
            if check == 'Rate Limit Exceeded':
                print('Rate Limit Exceeded, sleeping for 15 mins')
                exceed_counter += 1
                if exceed_counter >= 10:
                    exit('Over number of daily API requests\nRestart tomorrow')
                sleep(20)
                for i in range(15):
                    print(f'Sleep remaining: {int(15 - i)} minutes')
                    sleep(60)
                print('Recommencing...')
                latlong = requests.get(f"{url}&keys=latlng").json()
                time_list = requests.get(f"{url}&keys=time").json()
                altitude = requests.get(f"{url}&keys=altitude").json()
                break

        
        try:
            latlong = latlong[0]['data']
            start_coordinates = latlong[0]

            time_list = time_list[1]['data']
            altitude = altitude[1]['data']

            data = pd.DataFrame([*latlong], columns=['lat', 'long'])
            data['altitude'] = altitude
            start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
            data['time'] = [(start_time + timedelta(seconds=t))
                            for t in time_list]

            gpx = gpxpy.gpx.GPX()
            # Create first track in our GPX:
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(gpx_track)
            # Create first segment in our GPX track:
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            # Create points:
            for idx in data.index:
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
                    data.loc[idx, 'lat'], data.loc[idx, 'long'], elevation=data.loc[idx, 'altitude'],
                    time=data.loc[idx, 'time']))

            with open(f'{data_folder}/{strava_id}.gpx', 'w') as f:
                f.write(gpx.to_xml())
        except KeyError:
            return {'gpx_created': False, 'start_coordinates': None}
        except:
            return {
                'gpx_created': False,
                'start_coordinates': start_coordinates
            }

        return {'gpx_created': True, 'start_coordinates': start_coordinates}


def analyze_gpx(strava_id):
    try:
        gpx_file = open(f'gpx/{strava_id}.gpx', 'r')
    except FileNotFoundError:
        print(f"=========== {strava_id} file not found ===========")
        return {}
    print(f"======================= {strava_id} ======================= ")

    config = WaveConfigs.objects.get(id=1)

    min_speed_to_start_wave = config.min_speed_to_start_wave
    minimum_time_of_event_to_consider_wave = config.minimum_time_of_event_to_consider_wave

    gpx = gpxpy.parse(gpx_file)

    list_of_waves = []
    possible_wave = []
    for track in gpx.tracks:
        for segment in track.segments:

            for point_no, point in enumerate(segment.points):
                if point_no > 0:
                    speed_to_next_point = point.speed_between(segment.points[point_no - 1])
                    if speed_to_next_point:
                        speed_in_km_per_hour = convert_m_s_in_km_h(speed_to_next_point)

                        if speed_in_km_per_hour > min_speed_to_start_wave:
                            possible_wave.append(point)
                            # print(f"{display_hour(point.time)}|{display_speed(speed_in_km_per_hour)}km/h")

                        else:
                            # se não é superior a 9km/h vai ver se os pontos existentes são considerados uma onda
                            if len(possible_wave) >= minimum_time_of_event_to_consider_wave:
                                wave = get_wave_data(possible_wave, log=False)
                                if wave:
                                    list_of_waves.append(wave)
                            # reinicia a procura de onda
                            possible_wave = []

    return get_session_data(list_of_waves, log=False)


def determine_location(start_coordinates):
    best_match = SurfSpot.objects.get(id=1)
    best_diff = abs(float(best_match.latitude) - start_coordinates[0]) + abs(float(best_match.longitude) - start_coordinates[1])
    for spot in SurfSpot.objects.all():
        diff = abs(float(spot.latitude) - start_coordinates[0]) + abs(float(spot.longitude) - start_coordinates[1])
        if diff < best_diff:
            best_diff = diff
            best_match = spot
    return best_match

def get_session_data(waves, log=False):
    from datetime import timedelta
    max_speed = 0
    max_duration = timedelta(0, 0, 0)
    all_speeds = []
    all_wave_points = []
    for wave in waves:
        if wave['max_wave_speed'] > max_speed:
            max_speed = wave['max_wave_speed']
        if wave['duration'] > max_duration:
            max_duration = wave['duration']

        all_speeds.append(wave['speeds'])
        all_wave_points.append([{"latitude": p.latitude, "longitude": p.longitude, "time": p.time.strftime('%Y-%m-%d %H:%M:%S')} for p in wave['points']])
    if log:
        print(f"Number of waves: {len(waves)}!")
        print(f"Max Speed: {display_speed(max_speed)}")
        print(f"Longest wave: {max_duration.seconds}s")
        print("===========")
    return {
        'number_of_waves': len(waves),
        'max_speed': round(max_speed, 1),
        'max_duration': max_duration,
        'waves_speeds': all_speeds,
        'waves_points': all_wave_points

    }


def check_if_wave_is_valid(wave, array_of_speeds):
    return True


def get_wave_data(wave_points, log=False):
    qty_points = len(wave_points)
    duration = wave_points[qty_points-1].time - wave_points[0].time
    max_speed = 0
    sum_wave_speeds = 0
    array_of_speeds = []

    for wave_point_no, wave_point in enumerate(wave_points):
        if wave_point_no > 0:
            speed_to_next_wave_point = wave_point.speed_between(wave_points[wave_point_no - 1])
            sum_wave_speeds += speed_to_next_wave_point
            array_of_speeds.append(speed_to_next_wave_point)
            if speed_to_next_wave_point > max_speed:
                max_speed = speed_to_next_wave_point

    displayable_speeds = [display_speed(convert_m_s_in_km_h(speed)) for speed in array_of_speeds]
    if not check_if_wave_is_valid(wave_points, array_of_speeds):
        return None
    if log:
        print(f"Wave found at {display_hour(wave_points[0].time)}!")
        print(f"Duration: {duration.seconds}s")
        print(f"Qty wave points {len(wave_points)}")
        print(f"Absolute {abs(len(wave_points) - int(duration.seconds))}")
        print(f"Speeds: {displayable_speeds}")
        print(f"Max Speed: {display_speed(convert_m_s_in_km_h(max_speed))}")
        print(f"Avg Speed: {display_speed(convert_m_s_in_km_h(sum_wave_speeds/qty_points))}")
        print("===========")
    return {
        'points': wave_points,
        'duration': duration,
        'avg_wave_speed': convert_m_s_in_km_h(sum_wave_speeds/qty_points),
        'display_avg_wave_speed': display_speed(convert_m_s_in_km_h(sum_wave_speeds / qty_points)),
        'display_max_wave_speed': display_speed(convert_m_s_in_km_h(max_speed)),
        'max_wave_speed': convert_m_s_in_km_h(max_speed),
        'speeds': displayable_speeds
    }


def convert_m_s_in_km_h(speed_in_m_s):
    return speed_in_m_s * 3.6


def display_speed(speed_in_km_h):
    return f"{round(speed_in_km_h, 1)}km/h"


def display_hour(time_obj):
    return f"{time_obj.hour}:{time_obj.minute}:{time_obj.second}"
