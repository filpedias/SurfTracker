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
@login_required
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

    if request.method == 'POST':
        data = request.POST.copy()
        if 'client_id' in data and 'client_secret' in data:
            client_id = data['client_id']
            client_secret = data['client_secret']
            print(client_id, client_secret)

    
    vc = {
        'surfer': request.user
    }




    return render(request, 'strava_login.html', {'vc': vc})