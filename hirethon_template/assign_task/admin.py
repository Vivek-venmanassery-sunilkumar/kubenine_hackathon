from django.contrib import admin
from .models import TeamScheduleConfig, Schedule, Timeslot, ScheduleValidation


@admin.register(TeamScheduleConfig)
class TeamScheduleConfigAdmin(admin.ModelAdmin):
    list_display = ['team', 'timeslot_duration_hours', 'min_break_hours', 'created_at']
    list_filter = ['timeslot_duration_hours', 'created_at']
    search_fields = ['team__team_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['team', 'week_start_date', 'week_end_date', 'status', 'created_at']
    list_filter = ['status', 'week_start_date', 'created_at']
    search_fields = ['team__team_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'week_start_date'


@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ['schedule', 'assigned_member', 'start_datetime', 'end_datetime', 'is_break', 'duration_hours']
    list_filter = ['is_break', 'start_datetime', 'schedule__team']
    search_fields = ['assigned_member__name', 'assigned_member__email', 'schedule__team__team_name']
    readonly_fields = ['created_at', 'duration_hours']
    date_hierarchy = 'start_datetime'


@admin.register(ScheduleValidation)
class ScheduleValidationAdmin(admin.ModelAdmin):
    list_display = ['schedule', 'is_valid', 'has_sufficient_members', 'created_at']
    list_filter = ['is_valid', 'has_sufficient_members', 'created_at']
    search_fields = ['schedule__team__team_name']
    readonly_fields = ['created_at']