from django.urls import re_path, path, include
from django.conf import settings

from django.conf.urls.static import static
from django.contrib import admin
from . import views

urlpatterns = [
    # url(r'^admin_tools/', include('admin_tools.urls')),
    path('admin/', admin.site.urls),
    re_path(r'^user/login/$', views.login, name="login"),
    re_path(r'^user/logout/$', views.logout, name="logout"),
    re_path(r'^$', views.home, name="home"),
    re_path(r'^session/(?P<session_id>[0-9]+)/$', views.session, name="session")
]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns_i = [
    re_path('api/i/', include('main.urls_i'))
]

urlpatterns += urlpatterns_i
