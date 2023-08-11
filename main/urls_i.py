from django.urls import re_path
from main.views_i import StravaSync, ScanGPXs
urlpatterns = [
    re_path(r'strava/sync/$', StravaSync.as_view(), name="api_i_strava_sync"),
    re_path(r'gpx/scan/$', ScanGPXs.as_view(), name="api_i_scan_gpx")
]
