import json
import os
import requests
import time

from main.configs import client_id, client_secret, redirect_uri

def request_token(client_id, client_secret, code):
    response = requests.post(url='https://www.strava.com/oauth/token',
                             data={'client_id': client_id,
                                   'client_secret': client_secret,
                                   'code': code,
                                   'grant_type': 'authorization_code'})
    return response


def write_token(tokens):
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)


def get_token():
    with open('strava_tokens.json', 'r') as tokens:
        data = json.load(tokens)

    return data

def update_strava():


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

    data = get_token()

    if data['expires_at'] < time.time():
        new_tokens = request_token(client_id, client_secret, data['refresh_token'])
        if new_tokens.status_code == 200:
            # Update the file
            write_token(new_tokens)

    data = get_token()

    access_token = data['access_token']

    athlete_url = f"https://www.strava.com/api/v3/athlete?access_token={access_token}"
    try:
        response = requests.get(athlete_url)
        athlete = response.json()
        print(athlete)
    except ConnectionError as ce:
        print(ce)
        

    print('RESTful API:', athlete_url)
    print('=' * 5, 'ATHLETE INFO', '=' * 5)
    print('Name:', athlete['firstname'], " ", athlete['lastname'])
    print('Gender:', athlete['sex'])
    print('City:', athlete['city'], athlete['country'])
    print('Strava athlete from:', athlete['created_at'])

    activities_url = f"https://www.strava.com/api/v3/athlete/activities?" \
                    f"access_token={access_token}"
    print('RESTful API:', activities_url)
    response = requests.get(activities_url)
    if response.status_code == 200:
        activities = response.json()
        surfing_activities = list()

        for activity in activities:
            if 'type' in activity and activity['type'] == 'Surfing':
                surfing_activities.append(activity)

                print('=' * 5, 'SINGLE ACTIVITY', '=' * 5)
                print('Athlete:', athlete['firstname'], athlete['lastname'])
                print('Name:', activity['name'])
                print('Date:', activity['start_date'])
                print('Disance:', activity['distance'], 'm')
                print('Average Speed:', activity['average_speed'], 'm/s')
                print('Max speed:', activity['max_speed'], 'm/s')
                print('Moving time:', round(activity['moving_time'] / 60, 2), 'minutes')
                print('Location:', activity['location_city'],
                    activity['location_state'], activity['location_country'])
    else: 
        print(response)
