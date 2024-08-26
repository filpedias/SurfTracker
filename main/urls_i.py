from django.urls import re_path
from main.views_i import StravaSync, ScanGPXs, ProcessGPXData, LastDaysSessions
urlpatterns = [
    re_path(
        r'strava/sync/$', StravaSync.as_view(), name="api_i_strava_sync"
    ),
    re_path(
        r'gpx/scan/$', ScanGPXs.as_view(), name="api_i_scan_gpx"
    ),
    re_path(
        r'sessions/gpx_data/$', ProcessGPXData.as_view(),
        name="api_i_sessions_gpx_data"
    ),
    re_path(
        r'sessions/last_days/(?P<num_days_str>\w+)$', LastDaysSessions.as_view(),
        name="api_i_last_sessions"
    )
]
