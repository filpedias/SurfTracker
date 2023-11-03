import copy
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from main.settings import API_I_RESPONSE_TEMPLATE
from main.models import Surfer, SurfSession, SurfSpot, WaveConfigs, Wave, WavePoint
import requests
import json
import os


from datetime import datetime, timedelta, time as dt_time

from main.configs import client_id, client_secret, redirect_uri
# from gpxplotter import read_gpx_file, create_folium_map, add_segment_to_map


global access_token


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


def determine_duration(activity):
    activity_total_seconds = activity["elapsed_time"]
    minutes, seconds = divmod(activity_total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return dt_time(hours, minutes, seconds)


class StravaSync(APIView):

    access_token = ''
    

    permission_classes = [permissions.IsAuthenticated]

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
