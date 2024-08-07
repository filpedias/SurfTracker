from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpRequest, Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .models import Surfer, SurfSession, Wave, WavePoint
from main.forms import AuthenticateForm
from django.contrib.auth import authenticate, login as login_auth
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
                    login_auth(request=request, user=user)
                    return HttpResponseRedirect(next_page)
            else: 
                print("form not valid", form)


        else:
            # O form nao tem os campos necessarios
                form.add_error('password', _(u"Your account is blocked, please contact support"))
    else:
        # Pagina com o form de login
        form = AuthenticateForm(initial={'username': request.GET.get('username')})

    vc.update({
        'form': form,
        'next': next_page
    })
    return render(request, 'login.html', {'vc': vc})

from django.views.decorators.cache import never_cache
@never_cache
def logout(request):
    from django.contrib.auth import logout as logout_auth
    logout_auth(request)
    return HttpResponseRedirect('/')


@require_http_methods(["GET"])
@login_required
def home(request):
    
    surfer_sessions = SurfSession.objects.filter(surfer=request.user).order_by('-date')

    vc = {
        'surfer': request.user,
        'sessions': surfer_sessions,
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
        'wave_points': session.get_session_gpx()
    }
    vc = {
        'surfer': session.surfer,
        'session': session,
        'session_data': session_data     
    }

    return render(request, 'session.html', {'vc': vc})

