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

from main.configs import CLIENT_ID, CLIENT_SECRET
# from gpxplotter import read_gpx_file, create_folium_map, add_segment_to_map


global access_token


def write_token(tokens):
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)


def get_token():
    with open('strava_tokens.json', 'r') as tokens:
        data = json.load(tokens)

    return data


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
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):

        response = copy.deepcopy(API_I_RESPONSE_TEMPLATE)
        from main.strava import update_strava
        response = update_strava()
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


class ProcessGPXData(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):

        response = copy.deepcopy(API_I_RESPONSE_TEMPLATE)
        
        surfer_sessions = SurfSession.objects.filter(surfer=request.user) \
                            .order_by('-date')
        gpxs_data = []
        for s in surfer_sessions:
            gpx_session_waves = s.get_session_gpx()
            session_data = {
                'session_id': s.id,
                'name': s.name,
                'spot_lat': float(s.location.latitude),
                'spot_long': float(s.location.longitude),
                'wave_points': gpx_session_waves
            }
            gpxs_data.append(session_data)

        response["data"]["gpxs_data"] = gpxs_data
        response["status"] = "ok"

        return Response(response)
