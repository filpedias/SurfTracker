from django.contrib import admin
from main.models import Surfer, SurfSession, SurfSpot, Wave, WavePoint, WaveConfigs


@admin.register(Surfer)
class SurferAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'strava_user_id')


@admin.register(SurfSession)
class SurfSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'surfer', 'strava_activity_id', 'date', 'location')
    list_filter = ('surfer', 'date')


@admin.register(SurfSpot)
class SurfSpotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'latitude', 'longitude', 'is_saved')


@admin.register(Wave)
class WaveAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'duration', 'max_speed')
    list_filter = ['session']

    
@admin.register(WavePoint)
class WavePointAdmin(admin.ModelAdmin):
    list_display = ('id', 'wave', 'latitude', 'longitude', 'time')
    list_filter = ['wave']

@admin.register(WaveConfigs)
class WaveConfigsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_min_speed_to_start_wave', 'display_min_speed_to_stop_wave', 'minimum_time_of_event_to_consider_wave', 'display_min_max_speed_during_event_to_consider_wave')
    
