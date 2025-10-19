from django.urls import path
from .api.views import (
    team_schedule_config, update_team_schedule_config, team_schedule_status,
    generate_schedule, team_schedules, schedule_detail, publish_schedule,
    validate_schedule_endpoint, trigger_automatic_scheduling, scheduling_status,
    create_swap_request, get_swap_requests, accept_swap_request, reject_swap_request,
    get_team_schedule_for_swapping
)

app_name = 'assign_task'

urlpatterns = [
    # Team schedule configuration
    path('config/', team_schedule_config, name='team_schedule_config'),
    path('config/<int:config_id>/', update_team_schedule_config, name='update_team_schedule_config'),
    
    # Team schedule status and requirements
    path('status/<int:team_id>/', team_schedule_status, name='team_schedule_status'),
    
    # Schedule generation and management
    path('generate/<int:team_id>/', generate_schedule, name='generate_schedule'),
    path('schedules/<int:team_id>/', team_schedules, name='team_schedules'),
    path('schedule/<int:schedule_id>/', schedule_detail, name='schedule_detail'),
    path('schedule/<int:schedule_id>/publish/', publish_schedule, name='publish_schedule'),
    path('schedule/<int:schedule_id>/validate/', validate_schedule_endpoint, name='validate_schedule'),
    
    # Automatic scheduling
    path('auto/trigger/', trigger_automatic_scheduling, name='trigger_automatic_scheduling'),
    path('auto/status/', scheduling_status, name='scheduling_status'),
    
    # Swap requests
    path('swap/request/', create_swap_request, name='create_swap_request'),
    path('swap/requests/', get_swap_requests, name='get_swap_requests'),
    path('swap/<int:swap_id>/accept/', accept_swap_request, name='accept_swap_request'),
    path('swap/<int:swap_id>/reject/', reject_swap_request, name='reject_swap_request'),
    path('team/<int:team_id>/schedule/swap/', get_team_schedule_for_swapping, name='get_team_schedule_for_swapping'),
]
