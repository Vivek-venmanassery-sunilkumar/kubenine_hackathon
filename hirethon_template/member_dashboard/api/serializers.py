from rest_framework import serializers
from django.contrib.auth import get_user_model
from hirethon_template.assign_task.models import Timeslot, Schedule, SwapRequest
from hirethon_template.manager_dashboard.models import TeamMembers, Team
from hirethon_template.utils.error_handling import create_validation_error_response, create_not_found_error_response
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()


class TimeslotSerializer(serializers.ModelSerializer):
    """Serializer for timeslot data in member dashboard."""
    
    duration_hours = serializers.ReadOnlyField()
    team_name = serializers.CharField(source='schedule.team.team_name', read_only=True)
    assigned_member_name = serializers.SerializerMethodField()
    assigned_member_email = serializers.SerializerMethodField()
    is_my_slot = serializers.SerializerMethodField()
    can_swap = serializers.SerializerMethodField()
    swap_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Timeslot
        fields = [
            'id', 'start_datetime', 'end_datetime', 'duration_hours',
            'assigned_member', 'assigned_member_name', 'assigned_member_email',
            'is_break', 'team_name', 'is_my_slot', 'can_swap', 'swap_status', 'created_at'
        ]
    
    def get_assigned_member_name(self, obj):
        """Get the name of the assigned member."""
        if obj.assigned_member:
            return obj.assigned_member.name or obj.assigned_member.email
        return None
    
    def get_assigned_member_email(self, obj):
        """Get the email of the assigned member."""
        if obj.assigned_member:
            return obj.assigned_member.email
        return None
    
    def get_is_my_slot(self, obj):
        """Check if this timeslot is assigned to the current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.assigned_member == request.user
        return False
    
    def get_can_swap(self, obj):
        """Check if this timeslot can be swapped."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Can swap if:
        # 1. It's assigned to the current user
        # 2. It's not a break
        # 3. It's in the future
        # 4. There's no pending swap request for this slot
        if not obj.assigned_member or obj.assigned_member != request.user:
            return False
        
        if obj.is_break:
            return False
        
        if obj.start_datetime <= timezone.now():
            return False
        
        # Check if there's already a pending swap request for this slot
        has_pending_swap = SwapRequest.objects.filter(
            requester_slot=obj,
            status='pending'
        ).exists()
        
        return not has_pending_swap
    
    def get_swap_status(self, obj):
        """Get the swap status for this timeslot."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Check if there's a pending swap request where current user is the requester
        pending_request = SwapRequest.objects.filter(
            requester_slot=obj,
            requester=request.user,
            status='pending'
        ).first()
        
        if pending_request:
            return {
                'status': 'pending',
                'responder': pending_request.responder.name,
                'responder_email': pending_request.responder.email,
                'request_date': pending_request.request_date,
                'deadline': pending_request.deadline
            }
        
        # Check if there's a pending swap request where current user is the responder
        received_request = SwapRequest.objects.filter(
            responder_slot=obj,
            responder=request.user,
            status='pending'
        ).first()
        
        if received_request:
            return {
                'status': 'received',
                'requester': received_request.requester.name,
                'requester_email': received_request.requester.email,
                'request_date': received_request.request_date,
                'deadline': received_request.deadline
            }
        
        return None


class WeeklyScheduleSerializer(serializers.ModelSerializer):
    """Serializer for weekly schedule data."""
    
    timeslots = TimeslotSerializer(many=True, read_only=True)
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    week_dates = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'team_name', 'week_start_date', 'week_end_date',
            'status', 'timeslots', 'week_dates', 'created_at'
        ]
    
    def get_week_dates(self, obj):
        """Get all dates in the week."""
        dates = []
        current_date = obj.week_start_date
        for i in range(7):
            dates.append(current_date + timedelta(days=i))
        return dates


class SwapRequestSerializer(serializers.ModelSerializer):
    """Serializer for swap requests."""
    
    requester_name = serializers.CharField(source='requester.name', read_only=True)
    requester_email = serializers.CharField(source='requester.email', read_only=True)
    responder_name = serializers.CharField(source='responder.name', read_only=True)
    responder_email = serializers.CharField(source='responder.email', read_only=True)
    requester_slot_info = serializers.SerializerMethodField()
    responder_slot_info = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    can_be_accepted = serializers.ReadOnlyField()
    
    class Meta:
        model = SwapRequest
        fields = [
            'id', 'requester_name', 'requester_email', 'responder_name', 'responder_email',
            'requester_slot_info', 'responder_slot_info', 'status', 'request_date',
            'deadline', 'processed_at', 'rejection_reason', 'is_valid', 'can_be_accepted',
            'created_at'
        ]
        read_only_fields = ['id', 'request_date', 'processed_at', 'created_at']
    
    def get_requester_slot_info(self, obj):
        """Get requester slot information."""
        return {
            'id': obj.requester_slot.id,
            'start_datetime': obj.requester_slot.start_datetime,
            'end_datetime': obj.requester_slot.end_datetime,
            'duration_hours': obj.requester_slot.duration_hours,
            'team_name': obj.requester_slot.schedule.team.team_name
        }
    
    def get_responder_slot_info(self, obj):
        """Get responder slot information."""
        return {
            'id': obj.responder_slot.id,
            'start_datetime': obj.responder_slot.start_datetime,
            'end_datetime': obj.responder_slot.end_datetime,
            'duration_hours': obj.responder_slot.duration_hours,
            'team_name': obj.responder_slot.schedule.team.team_name
        }


class SwapRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating swap requests."""
    
    requester_slot = serializers.PrimaryKeyRelatedField(queryset=Timeslot.objects.all())
    responder_slot_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = SwapRequest
        fields = ['requester_slot', 'responder_slot_id']
    
    def validate_requester_slot(self, value):
        """Validate the requester slot."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")
        
        # Check if the slot is assigned to the current user
        if not value.assigned_member or value.assigned_member != request.user:
            raise serializers.ValidationError("You can only request swaps for your own slots.")
        
        # Check if the slot is in the future
        if value.start_datetime <= timezone.now():
            raise serializers.ValidationError("You can only request swaps for future slots.")
        
        # Check if it's not a break
        if value.is_break:
            raise serializers.ValidationError("You cannot swap break periods.")
        
        # Check if there's already a pending swap request for this slot
        if SwapRequest.objects.filter(requester_slot=value, status='pending').exists():
            raise serializers.ValidationError("A swap request is already pending for this slot.")
        
        return value
    
    def validate_responder_slot_id(self, value):
        """Validate the responder slot ID."""
        try:
            responder_slot = Timeslot.objects.get(id=value)
        except Timeslot.DoesNotExist:
            raise serializers.ValidationError("Responder slot not found.")
        
        # Check if the slot is assigned to someone
        if not responder_slot.assigned_member:
            raise serializers.ValidationError("The responder slot is not assigned to anyone.")
        
        # Check if the slot is in the future
        if responder_slot.start_datetime <= timezone.now():
            raise serializers.ValidationError("You can only request swaps for future slots.")
        
        # Check if it's not a break
        if responder_slot.is_break:
            raise serializers.ValidationError("You cannot swap break periods.")
        
        # Check if there's already a pending swap request for this slot
        if SwapRequest.objects.filter(responder_slot=responder_slot, status='pending').exists():
            raise serializers.ValidationError("A swap request is already pending for this slot.")
        
        return value
    
    def validate(self, data):
        """Validate the swap request."""
        requester_slot = data.get('requester_slot')
        responder_slot_id = data.get('responder_slot_id')
        
        if requester_slot and responder_slot_id:
            try:
                responder_slot = Timeslot.objects.get(id=responder_slot_id)
            except Timeslot.DoesNotExist:
                raise serializers.ValidationError("Responder slot not found.")
            
            # Check if both slots are from the same team
            if requester_slot.schedule.team != responder_slot.schedule.team:
                raise serializers.ValidationError("Both slots must be from the same team.")
            
            # Check if requester and responder are different
            if requester_slot.assigned_member == responder_slot.assigned_member:
                raise serializers.ValidationError("You cannot swap with yourself.")
            
            # Check if there's already a swap request between these slots
            if SwapRequest.objects.filter(
                requester_slot=requester_slot,
                responder_slot=responder_slot
            ).exists():
                raise serializers.ValidationError("A swap request already exists between these slots.")
        
        return data
    
    def create(self, validated_data):
        """Create the swap request."""
        request = self.context.get('request')
        responder_slot_id = validated_data.pop('responder_slot_id')
        responder_slot = Timeslot.objects.get(id=responder_slot_id)
        
        # Set the deadline to 24 hours before the first slot starts
        requester_slot = validated_data['requester_slot']
        first_slot_start = min(requester_slot.start_datetime, responder_slot.start_datetime)
        deadline = first_slot_start - timedelta(hours=24)
        
        # Remove requester_slot from validated_data since we're passing it explicitly
        validated_data.pop('requester_slot', None)
        
        swap_request = SwapRequest.objects.create(
            requester=request.user,
            responder=responder_slot.assigned_member,
            requester_slot=requester_slot,
            responder_slot=responder_slot,
            deadline=deadline,
            **validated_data
        )
        
        return swap_request


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for team members."""
    
    member_name = serializers.CharField(source='member.name', read_only=True)
    member_email = serializers.CharField(source='member.email', read_only=True)
    
    class Meta:
        model = TeamMembers
        fields = ['id', 'member_name', 'member_email', 'joined_at', 'is_active']
