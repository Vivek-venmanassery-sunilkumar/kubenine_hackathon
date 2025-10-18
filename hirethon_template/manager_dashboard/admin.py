from django.contrib import admin
from hirethon_template.manager_dashboard.models import Team, Invitation, TeamMembers


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'organization', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at']
    search_fields = ['team_name', 'organization__org_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['team_name']


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'team', 'organization', 'invited_by', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'team', 'organization', 'created_at', 'expires_at']
    search_fields = ['email', 'team__team_name', 'organization__org_name', 'invited_by__name']
    readonly_fields = ['token', 'created_at', 'accepted_at']
    ordering = ['-created_at']


@admin.register(TeamMembers)
class TeamMembersAdmin(admin.ModelAdmin):
    list_display = ['member', 'team', 'is_active', 'joined_at']
    list_filter = ['is_active', 'team', 'joined_at']
    search_fields = ['member__name', 'member__email', 'team__team_name']
    readonly_fields = ['joined_at']
    ordering = ['-joined_at']
