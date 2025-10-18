from rest_framework import serializers
from django.contrib.auth import get_user_model
from hirethon_template.manager_dashboard.models import Team, Invitation, TeamMembers
from hirethon_template.authentication.models import Organization

User = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model."""
    
    organization_name = serializers.CharField(source='organization.org_name', read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'team_name', 'organization_name', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['organization']  # Organization is auto-assigned, not user input


class TeamListSerializer(serializers.ModelSerializer):
    """Serializer for listing teams."""
    
    organization_name = serializers.CharField(source='organization.org_name', read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'team_name', 'organization_name', 'created_at', 'is_active']


class ManagerDashboardSerializer(serializers.Serializer):
    """
    Serializer for manager dashboard data.
    """
    message = serializers.CharField()
    status = serializers.CharField()


class ManagerStatsSerializer(serializers.Serializer):
    """
    Serializer for manager dashboard statistics.
    """
    total_teams = serializers.IntegerField(required=False)
    total_members = serializers.IntegerField(required=False)
    active_teams = serializers.IntegerField(required=False)
    organization_name = serializers.CharField(required=False)


class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for Invitation model."""
    
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    organization_name = serializers.CharField(source='organization.org_name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.name', read_only=True)
    invitation_url = serializers.CharField(source='get_invitation_url', read_only=True)
    is_expired = serializers.BooleanField(source='is_expired', read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'token', 'team', 'team_name', 'organization_name', 'invited_by_name',
            'status', 'created_at', 'expires_at', 'accepted_at', 
            'invitation_url', 'is_expired'
        ]
        read_only_fields = ['token', 'invited_by', 'organization', 'created_at', 'accepted_at']


class InvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invitations."""
    
    class Meta:
        model = Invitation
        fields = ['email', 'team']
    
    def validate_team(self, value):
        """Validate that the team belongs to the manager's organization."""
        user = self.context['request'].user
        if user.role == 'manager':
            try:
                organization = Organization.objects.get(manager=user)
                if value.organization != organization:
                    raise serializers.ValidationError("You can only invite members to teams in your organization.")
                if not value.is_active:
                    raise serializers.ValidationError("You can only invite members to active teams.")
            except Organization.DoesNotExist:
                raise serializers.ValidationError("Manager is not assigned to any organization.")
        return value
    
    def create(self, validated_data):
        """Create invitation with manager's organization."""
        user = self.context['request'].user
        if user.role == 'manager':
            try:
                organization = Organization.objects.get(manager=user)
                validated_data['organization'] = organization
                validated_data['invited_by'] = user
                # Set expiration to 7 days from now
                from django.utils import timezone
                from datetime import timedelta
                validated_data['expires_at'] = timezone.now() + timedelta(days=7)
                return super().create(validated_data)
            except Organization.DoesNotExist:
                raise serializers.ValidationError("Manager is not assigned to any organization.")
        else:
            raise serializers.ValidationError("Only managers can send invitations.")


class InvitationListSerializer(serializers.ModelSerializer):
    """Serializer for listing invitations."""
    
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    organization_name = serializers.CharField(source='organization.org_name', read_only=True)
    is_expired = serializers.BooleanField(source='is_expired', read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'team_name', 'organization_name', 'status', 
            'created_at', 'expires_at', 'accepted_at', 'is_expired'
        ]


class TeamMembersSerializer(serializers.ModelSerializer):
    """Serializer for TeamMembers model."""
    
    member_name = serializers.CharField(source='member.name', read_only=True)
    member_email = serializers.CharField(source='member.email', read_only=True)
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    
    class Meta:
        model = TeamMembers
        fields = ['id', 'team', 'team_name', 'member', 'member_name', 'member_email', 'joined_at', 'is_active']
        read_only_fields = ['joined_at']
