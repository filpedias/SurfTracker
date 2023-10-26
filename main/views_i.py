import copy
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from main.settings import API_I_RESPONSE_TEMPLATE
from main.models import Surfer, SurfSession, SurfSpot, WaveConfigs, Wave, WavePoint
import requests
import json
import os
from time import time, sleep
import pandas as pd
import gpxpy.gpx
from datetime import datetime, timedelta, time as dt_time
import gpxpy
from main.configs import client_id, client_secret, redirect_uri
# from gpxplotter import read_gpx_file, create_folium_map, add_segment_to_map


global access_token


def analyze_gpx(strava_id):
    gpx_file = open(f'gpx/{strava_id}.gpx', 'r')
    print(f"======================= {strava_id} ======================= ")

    config = WaveConfigs.objects.get(id=1)
    
    min_speed_to_start_wave = config.min_speed_to_start_wave
    minimum_time_of_event_to_consider_wave = config.minimum_time_of_event_to_consider_wave

    gpx = gpxpy.parse(gpx_file)

    all_registed_speeds = list()
    list_of_waves = list()
    possible_wave = list()
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
                            possible_wave = list()

    return get_session_data(list_of_waves, log=False)


def write_token(tokens):
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)


def get_token():
    with open('strava_tokens.json', 'r') as tokens:
        data = json.load(tokens)

    return data


def request_token(client_id, client_secret, code):
    try:
        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
    except ConnectionError as ce:
        print(ce)

    return response

def refresh_token(client_id, client_secret, refresh_token):
    try:
        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )
    except ConnectionError as ce:
        print(ce)

    return response


def convert_m_s_in_km_h(speed_in_m_s):
    return speed_in_m_s * 3.6


def display_speed(speed_in_km_h):
    return f"{round(speed_in_km_h, 1)}km/h"


def display_hour(time):
    return f"{time.hour}:{time.minute}:{time.second}"


def check_if_wave_is_valid(wave, array_of_speeds):
    return True


def get_wave_data(wave_points, log=False):
    qty_points = len(wave_points)
    duration = wave_points[qty_points-1].time - wave_points[0].time
    max_speed = 0
    sum_wave_speeds = 0
    array_of_speeds = list()

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


def get_session_data(waves, log=False):
    from datetime import timedelta
    max_speed = 0
    max_duration = timedelta(0, 0, 0)
    all_speeds = list()
    all_wave_points = list()
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


def determine_location(start_coordinates):
    best_match = SurfSpot.objects.get(id=1)
    best_diff = abs(float(best_match.latitude) - start_coordinates[0]) + abs(float(best_match.longitude) - start_coordinates[1])
    for spot in SurfSpot.objects.all():
        diff = abs(float(spot.latitude) - start_coordinates[0]) + abs(float(spot.longitude) - start_coordinates[1])
        if diff < best_diff:
            best_diff = diff
            best_match = spot
    return best_match


def determine_duration(activity):
    activity_total_seconds = activity["elapsed_time"]
    minutes, seconds = divmod(activity_total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return dt_time(hours, minutes, seconds)


class StravaSync(APIView):

    access_token = ''
    data_folder = 'gpx/'
    exceed_counter = 0

    permission_classes = [permissions.IsAuthenticated]
    
    def get_activity_analysis_data(self, activity):
        gpx_creation = self.create_gpx_activity_file(activity)

        gpx_analysis = analyze_gpx(activity['id'])

        return {
            'location': determine_location(gpx_creation['start_coordinates']),
            'gpx_created': gpx_creation['gpx_created'],
            'number_of_waves': gpx_analysis['number_of_waves'],
            'max_speed': gpx_analysis['max_speed'],
            'waves_speeds': gpx_analysis['waves_speeds'],
            'waves_points': gpx_analysis['waves_points']

        }

    def get_surfing_activities_from_strava(self, activities, surfer):

        new_surf_activities = list()

        surf_sessions = SurfSession.objects.filter(surfer=surfer).values_list('strava_activity_id', flat=True)

        for activity in activities:
            if activity['type'] == 'Surfing':
                if str(activity['id']) not in surf_sessions:
                    activity_duration = determine_duration(activity)
                    if activity_duration > dt_time(0, 20):
                        activity_analysis = self.get_activity_analysis_data(activity)
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
                                wp.time = datetime.strptime(wave_point['time'], '%Y-%m-%d %H:%M:%S')
                                wp.save()

                        new_surf_activities.append(s)

        return new_surf_activities

    def create_gpx_activity_file(self, activity):

        strava_id = activity['id']
        start_time = activity['start_date']

        url = f"https://www.strava.com/api/v3/activities/{strava_id}/streams?" \
              f"access_token={self.acess_token}"
        latlong = requests.get(f"{url}&keys=latlng").json()
        time_list = requests.get(f"{url}&keys=time").json()
        altitude = requests.get(f"{url}&keys=altitude").json()
        for r in [latlong, time_list, altitude]:
            if isinstance(r, dict) and 'message' in r.keys():
                check = r['message']
                if check == 'Rate Limit Exceeded':
                    print('Rate Limit Exceeded, sleeping for 15 mins')
                    self.exceed_counter += 1
                    if self.exceed_counter >= 10:
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

        latlong = latlong[0]['data']
        start_coordinates = latlong[0]
        try:
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

            with open(f'{self.data_folder}/{strava_id}.gpx', 'w') as f:
                f.write(gpx.to_xml())
        except:
            return {'gpx_created': False, 'start_coordinates': start_coordinates}

        return {'gpx_created': True, 'start_coordinates': start_coordinates}

    def get(self, request, format=None):

        response = copy.deepcopy(API_I_RESPONSE_TEMPLATE)
        response["status"] = "ok"

        if not os.path.exists('strava_tokens.json'):
            request_url = f'http://www.strava.com/oauth/authorize?client_id={client_id}' \
                          f'&response_type=code&redirect_uri={redirect_uri}' \
                          f'&scope=profile:read_all,activity:read_all'

            print('Click here:', request_url)
            print('Please authorize the app and copy&paste below the generated code!')
            print('P.S: you can find the code in the URL')
            code = input('Insert the code from the url: ')

            tokens = request_token(client_id, client_secret, code)

            # Save json response as a variable
            strava_tokens = tokens.json()
            # Save tokens to file
            write_token(strava_tokens)

        else:
            code = "a0d6acdc6d81a4f36df1eaeeae94e27b2b28ff4c"
        data = get_token()

        if data['expires_at'] < time():
            new_tokens = refresh_token(client_id, client_secret, data['refresh_token'])
            # Update the file
            write_token(new_tokens)

        data = get_token()

        self.acess_token = data['access_token']

        athlete_url = f"https://www.strava.com/api/v3/athlete?" \
                      f"access_token={self.acess_token}"
        athlete_response = requests.get(athlete_url)
        athlete = athlete_response.json()

        activities_url = f"https://www.strava.com/api/v3/athlete/activities?" \
                         f"access_token={self.acess_token}"
        print('RESTful API:', activities_url)
        response_activities = requests.get(activities_url)
        surfer_obj = Surfer.objects.get(strava_user_id=athlete['id'])

        new_sessions_added = list()
        if surfer_obj:
            new_sessions_added = self.get_surfing_activities_from_strava(response_activities.json(), surfer_obj)

        response['msg'] = f"{len(new_sessions_added)} new sessions added" if len(new_sessions_added) > 0 \
            else "Everything was already updated"

        return Response(response)


class ScanGPXs(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):

        response = copy.deepcopy(API_I_RESPONSE_TEMPLATE)
        response["status"] = "ok"

        sessions = SurfSession.objects.all()
        updated_sessions = list()
        for session in sessions:
            gpx_analysis = analyze_gpx(session.strava_activity_id)

            session.number_of_waves = gpx_analysis['number_of_waves']
            session.max_speed = gpx_analysis['max_speed']
            session.save()
            updated_sessions.append({
                "name": session.name,
                "max_speed": session.max_speed,
                "number_of_waves": session.number_of_waves,
                'waves_speeds': gpx_analysis['waves_speeds'],
                'waves_points': gpx_analysis['waves_points']
            })

        response['msg'] = f"{sessions.count()} sessions updaded" if sessions.count() > 0 \
            else "No sessions on system"

        response['updated_sessions'] = updated_sessions

        return Response(response)
