from rest_framework import serializers
from ..models import TeamScheduleConfig, Schedule, Timeslot, ScheduleValidation, SwapRequest
from hirethon_template.manager_dashboard.models import Team
from django.contrib.auth import get_user_model

User = get_user_model()


class TeamScheduleConfigSerializer(serializers.ModelSerializer):
    """Serializer for team schedule configuration."""
    
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    max_daily_hours = serializers.ReadOnlyField()
    max_weekly_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = TeamScheduleConfig
        fields = [
            'id', 'team', 'team_name', 'timeslot_duration_hours', 
            'min_break_hours', 'max_daily_hours', 'max_weekly_hours',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_timeslot_duration_hours(self, value):
        if value > 8:
            raise serializers.ValidationError("Timeslot duration cannot exceed 8 hours")
        if value <= 0:
            raise serializers.ValidationError("Timeslot duration must be positive")
        return value
    
    def validate_min_break_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("Minimum break hours must be positive")
        if value > 24:
            raise serializers.ValidationError("Minimum break hours cannot exceed 24 hours")
        return value


class TimeslotSerializer(serializers.ModelSerializer):
    """Serializer for timeslots."""
    
    assigned_member_name = serializers.CharField(source='assigned_member.name', read_only=True)
    assigned_member_email = serializers.CharField(source='assigned_member.email', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = Timeslot
        fields = [
            'id', 'schedule', 'assigned_member', 'assigned_member_name', 
            'assigned_member_email', 'start_datetime', 'end_datetime', 
            'is_break', 'duration_hours', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ScheduleValidationSerializer(serializers.ModelSerializer):
    """Serializer for schedule validation results."""
    
    class Meta:
        model = ScheduleValidation
        fields = [
            'id', 'schedule', 'is_valid', 'has_sufficient_members',
            'validation_errors', 'validation_warnings', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for schedules."""
    
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    timeslots = TimeslotSerializer(many=True, read_only=True)
    validation = ScheduleValidationSerializer(read_only=True)
    total_timeslots = serializers.SerializerMethodField()
    assigned_timeslots = serializers.SerializerMethodField()
    unassigned_timeslots = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'team', 'team_name', 'week_start_date', 'week_end_date',
            'status', 'timeslots', 'validation', 'total_timeslots',
            'assigned_timeslots', 'unassigned_timeslots', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_timeslots(self, obj):
        return obj.timeslots.count()
    
    def get_assigned_timeslots(self, obj):
        return obj.timeslots.filter(assigned_member__isnull=False).count()
    
    def get_unassigned_timeslots(self, obj):
        return obj.timeslots.filter(assigned_member__isnull=True, is_break=False).count()


class ScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new schedules."""
    
    class Meta:
        model = Schedule
        fields = ['team', 'week_start_date', 'status']
    
    def validate_week_start_date(self, value):
        # Ensure it's a Monday
        if value.weekday() != 0:
            raise serializers.ValidationError("Week start date must be a Monday")
        return value


class TeamScheduleStatusSerializer(serializers.ModelSerializer):
    """Serializer for team schedule status and requirements."""
    
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    member_count = serializers.SerializerMethodField()
    required_members = serializers.SerializerMethodField()
    can_generate_schedule = serializers.SerializerMethodField()
    current_schedule = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamScheduleConfig
        fields = [
            'id', 'team', 'team_name', 'timeslot_duration_hours', 
            'min_break_hours', 'member_count', 'required_members',
            'can_generate_schedule', 'current_schedule'
        ]
    
    def get_member_count(self, obj):
        member_count = obj.team.members.filter(is_active=True).count()
        print(f"DEBUG: Team {obj.team.team_name} has {member_count} active members")
        return member_count
    
    def get_required_members(self, obj):
        """Get minimum members needed to start scheduling."""
        return obj.get_min_team_size_for_scheduling()
    
    def get_can_generate_schedule(self, obj):
        """Check if team has enough members to generate a schedule."""
        member_count = self.get_member_count(obj)
        required_members = self.get_required_members(obj)
        return member_count >= required_members
    
    def get_current_schedule(self, obj):
        """Get the current week's schedule if it exists."""
        from datetime import date
        from django.utils import timezone
        
        # Get current week's Monday
        from datetime import timedelta
        today = timezone.now().date()
        days_since_monday = today.weekday()
        current_week_monday = today - timedelta(days=days_since_monday)
        
        try:
            current_schedule = Schedule.objects.get(
                team=obj.team,
                week_start_date=current_week_monday
            )
            return ScheduleSerializer(current_schedule).data
        except Schedule.DoesNotExist:
            return None


class SwapRequestSerializer(serializers.ModelSerializer):
    """Serializer for swap requests."""
    
    requester_name = serializers.CharField(source='requester.name', read_only=True)
    responder_name = serializers.CharField(source='responder.name', read_only=True)
    requester_slot_details = serializers.SerializerMethodField()
    responder_slot_details = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    can_be_accepted = serializers.SerializerMethodField()
    
    class Meta:
        model = SwapRequest
        fields = [
            'id', 'requester', 'requester_name', 'responder', 'responder_name',
            'requester_slot', 'requester_slot_details', 'responder_slot', 'responder_slot_details',
            'status', 'request_date', 'deadline', 'processed_at', 'rejection_reason',
            'is_valid', 'can_be_accepted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'processed_at']
    
    def get_requester_slot_details(self, obj):
        """Get details of the requester's slot."""
        return {
            'id': obj.requester_slot.id,
            'start_datetime': obj.requester_slot.start_datetime,
            'end_datetime': obj.requester_slot.end_datetime,
            'duration_hours': obj.requester_slot.duration_hours,
            'assigned_member_name': obj.requester_slot.assigned_member.name if obj.requester_slot.assigned_member else None
        }
    
    def get_responder_slot_details(self, obj):
        """Get details of the responder's slot."""
        return {
            'id': obj.responder_slot.id,
            'start_datetime': obj.responder_slot.start_datetime,
            'end_datetime': obj.responder_slot.end_datetime,
            'duration_hours': obj.responder_slot.duration_hours,
            'assigned_member_name': obj.responder_slot.assigned_member.name if obj.responder_slot.assigned_member else None
        }
    
    def get_is_valid(self, obj):
        """Check if the swap request is still valid."""
        return obj.is_valid()
    
    def get_can_be_accepted(self, obj):
        """Check if the swap can be accepted."""
        return obj.can_be_accepted()
    
    def validate(self, data):
        """Validate the swap request."""
        requester = data.get('requester')
        responder = data.get('responder')
        requester_slot = data.get('requester_slot')
        responder_slot = data.get('responder_slot')
        
        # Check if both members are in the same team
        if requester and responder and requester_slot and responder_slot:
            requester_team = requester_slot.schedule.team
            responder_team = responder_slot.schedule.team
            
            if requester_team != responder_team:
                raise serializers.ValidationError("Both members must be in the same team")
            
            # Check if both slots are in the same week
            if requester_slot.schedule.week_start_date != responder_slot.schedule.week_start_date:
                raise serializers.ValidationError("Both slots must be in the same week")
            
            # Check if requester owns the requester slot
            if requester_slot.assigned_member != requester:
                raise serializers.ValidationError("Requester must own the requester slot")
            
            # Check if responder owns the responder slot
            if responder_slot.assigned_member != responder:
                raise serializers.ValidationError("Responder must own the responder slot")
            
            # Check if both members are active
            from hirethon_template.manager_dashboard.models import TeamMembers
            requester_membership = TeamMembers.objects.filter(
                team=requester_team, member=requester, is_active=True
            ).exists()
            responder_membership = TeamMembers.objects.filter(
                team=responder_team, member=responder, is_active=True
            ).exists()
            
            if not requester_membership:
                raise serializers.ValidationError("Requester is not an active team member")
            if not responder_membership:
                raise serializers.ValidationError("Responder is not an active team member")
        
        return data


class SwapRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating swap requests."""
    
    class Meta:
        model = SwapRequest
        fields = ['requester', 'responder', 'requester_slot', 'responder_slot']
    
    def create(self, validated_data):
        """Create a swap request with deadline calculation."""
        from django.utils import timezone
        from datetime import timedelta
        
        requester_slot = validated_data['requester_slot']
        responder_slot = validated_data['responder_slot']
        
        # Calculate deadline: 24 hours before the first slot starts
        first_slot_start = min(
            requester_slot.start_datetime,
            responder_slot.start_datetime
        )
        deadline = first_slot_start - timedelta(hours=24)
        
        # Create the swap request
        swap_request = SwapRequest.objects.create(
            deadline=deadline,
            **validated_data
        )
        
        return swap_request
