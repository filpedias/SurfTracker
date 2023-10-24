from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpRequest, Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .models import Surfer, SurfSession, Wave, WavePoint
from main.forms import AuthenticateForm
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from main.settings import STRAVA_AUTH_URL, STRAVA_TOKEN_URL, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
import main.strava

def login(request):
    vc = {}
    user = request.user
    if user.is_authenticated:
        return HttpResponseRedirect('/')

    next_page = reverse('home', args=())
    if 'next' in request.GET:
        next_page = request.GET['next']

    if request.method == 'POST':

        data = request.POST.copy()
        if 'username' in data and 'password' in data:
            username = data['username']

            form = AuthenticateForm(data)
            if form.is_valid():
                user_auth = authenticate(email=username, password=form.cleaned_data['password'])
                if user_auth is None:
                    user = Surfer.objects.get(username=username)
                    request.user = user
                    request.method = 'GET'
                    return home(request)


        else:
            # O form nao tem os campos necessarios
                return HttpResponseRedirect('/')
    else:
        # Pagina com o form de login
        form = AuthenticateForm(initial={'username': request.GET.get('username')})

    vc.update({
        'form': form,
        'next': next_page
    })
    return render(request, 'login.html', {'vc': vc})


@login_required
def logout_view(request):
    vc = {}
    logout(request)
    return render(request, 'home.html', {'vc': vc})


def get_session_gpx(s):
    gpx_session_waves = list()
    session_waves = Wave.objects.filter(session=s)
    for w in session_waves:
        session_wave_gpx = list()
        session_wave = WavePoint.objects.filter(wave=w)
        for wp in session_wave:
            session_wave_gpx.append({
                "latitude": float(wp.latitude),
                "longitude": float(wp.longitude),
                "time": wp.time.strftime('%Y-%m-%d %H:%M:%S'),
            })
            gpx_session_waves.append(session_wave_gpx)
    
    return gpx_session_waves
    
@require_http_methods(["GET"])
@login_required
def home(request):

    surfer_sessions = SurfSession.objects.filter(surfer=request.user).order_by('-date')
    gpxs_data = []
    for s in surfer_sessions:
        
        gpx_session_waves = get_session_gpx(s)
        session_data = {
            'session_id': s.id,
            'name': s.name,
            'spot_lat': float(s.location.latitude),
            'spot_long': float(s.location.longitude),
            'wave_points': gpx_session_waves
        }
        gpxs_data.append(session_data)

    vc = {
        'surfer': request.user,
        'sessions': surfer_sessions, 
        'gpxs_data': gpxs_data
    }

    return render(request, 'home.html', {'vc': vc})


@require_http_methods(["GET"])
def session(request, session_id):

    session = SurfSession.objects.get(id=session_id)
    session_data = {
        'session_id': session.id,
        'name': session.name,
        'spot_lat': float(session.location.latitude),
        'spot_long': float(session.location.longitude),
        'wave_points': get_session_gpx(session)
    }
    vc = {
        'surfer': session.surfer,
        'session': session,
        'session_data': session_data     
    }

    return render(request, 'session.html', {'vc': vc})


    
@require_http_methods(["GET", "POST"])
def strava_login(request):
    from django.shortcuts import redirect, render



    if request.method == 'POST':
        data = request.POST.copy()
        if 'client_id' in data and 'client_secret' in data:
            client_id = data['client_id']
            client_secret = data['client_secret']
            print(client_id, client_secret)
            params = {
                'client_id': client_id,
                'redirect_uri': request.build_absolute_uri(reverse('strava_callback')),
                'response_type': 'code',
                'scope': 'read',
            }
            auth_url = f'{STRAVA_AUTH_URL}?{"&".join([f"{k}={v}" for k, v in params.items()])}'
            return redirect(auth_url)

    
    vc = {
        'surfer': request.user
    }




    return render(request, 'strava_login.html', {'vc': vc})


def strava_callback(request):
    import requests

    code = request.GET.get('code')
    if code:
        data = {
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
        }
        response = requests.post(url='https://www.strava.com/oauth/token',
                             data={'client_id': STRAVA_CLIENT_ID,
                                   'client_secret': STRAVA_CLIENT_SECRET,
                                   'code': code,
                                   'grant_type': 'authorization_code'})
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            
            athlete_url = f"https://www.strava.com/api/v3/athlete?" \
                        f"access_token={access_token}"
            athlete_response = requests.get(athlete_url)
            athlete = athlete_response.json()

            activities_url = f"https://www.strava.com/api/v3/athlete/activities?" \
                            f"access_token={access_token}"
            print('RESTful API:', activities_url)
            response_activities = requests.get(activities_url)
            surfer_obj = Surfer.objects.get(strava_user_id=athlete['id'])

            new_sessions_added = list()
            if surfer_obj:
                new_sessions_added = strava.get_surfing_activities_from_strava(response_activities.json(), surfer_obj)

            response['msg'] = f"{len(new_sessions_added)} new sessions added" if len(new_sessions_added) > 0 \
                else "Everything was already updated"


    return render(request, 'strava_error.html')