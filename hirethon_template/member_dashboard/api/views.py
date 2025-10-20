from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from hirethon_template.authentication.api.permissions import IsMemberOrManager
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from hirethon_template.assign_task.models import Timeslot, Schedule, SwapRequest
from hirethon_template.manager_dashboard.models import TeamMembers, Team
from hirethon_template.authentication.models import Organization
from hirethon_template.member_dashboard.api.serializers import (
    TimeslotSerializer, WeeklyScheduleSerializer, SwapRequestSerializer, 
    SwapRequestCreateSerializer, TeamMemberSerializer
)
from hirethon_template.utils.error_handling import (
    create_success_response, create_validation_error_response,
    create_not_found_error_response, create_internal_error_response,
    create_unauthorized_error_response
)
from hirethon_template.authentication.api.permissions import IsMemberOrManager
from hirethon_template.users.enums.role_choices import UserRole

User = get_user_model()


class MemberScheduleViewSet(viewsets.ViewSet):
    """ViewSet for member schedule management."""
    
    permission_classes = [IsMemberOrManager]
    
    def get_queryset(self):
        """Get timeslots for the current user's teams."""
        user = self.request.user
        
        # Get teams based on user role
        if user.role == UserRole.ADMIN:
            # Admins can see all teams
            user_teams = None  # Will be handled in the filter
        elif user.role == UserRole.MANAGER:
            # Managers can see teams from organizations they manage
            manager_orgs = Organization.objects.filter(
                manager=user,
                is_active=True
            ).values_list('id', flat=True)
            user_teams = Team.objects.filter(
                organization__in=manager_orgs,
                is_active=True
            ).values_list('id', flat=True)
        else:
            # Members can see teams they're members of
            user_teams = TeamMembers.objects.filter(
                member=user,
                is_active=True
            ).values_list('team', flat=True)
        
        # Get timeslots for the next 7 days
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        # Build the filter based on user role
        filter_kwargs = {
            'start_datetime__date__gte': today,
            'start_datetime__date__lt': next_week
        }
        
        if user_teams is not None:
            filter_kwargs['schedule__team__in'] = user_teams
        
        return Timeslot.objects.filter(
            **filter_kwargs
        ).select_related(
            'schedule__team', 'assigned_member'
        ).order_by('start_datetime')
    
    def list(self, request):
        """Get member's schedule for the next 7 days."""
        try:
            timeslots = self.get_queryset()
            serializer = TimeslotSerializer(timeslots, many=True, context={'request': request})
            
            # Group timeslots by date
            schedule_by_date = {}
            for timeslot in timeslots:
                date_key = timeslot.start_datetime.date().isoformat()
                if date_key not in schedule_by_date:
                    schedule_by_date[date_key] = []
                schedule_by_date[date_key].append(timeslot)
            
            # Serialize grouped data
            serialized_schedule = {}
            for date_key, date_timeslots in schedule_by_date.items():
                serialized_schedule[date_key] = TimeslotSerializer(
                    date_timeslots, many=True, context={'request': request}
                ).data
            
            return create_success_response(
                "Schedule retrieved successfully.",
                {
                    "schedule": serialized_schedule,
                    "date_range": {
                        "start": timezone.now().date().isoformat(),
                        "end": (timezone.now().date() + timedelta(days=6)).isoformat()
                    }
                }
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve schedule. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=False, methods=['get'])
    def my_slots(self, request):
        """Get only the current user's assigned slots."""
        try:
            timeslots = self.get_queryset().filter(assigned_member=request.user)
            serializer = TimeslotSerializer(timeslots, many=True, context={'request': request})
            
            return create_success_response(
                "Your slots retrieved successfully.",
                {"slots": serializer.data}
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve your slots. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=False, methods=['get'])
    def team_schedule(self, request):
        """Get the full team schedule for the next 7 days."""
        try:
            user = request.user
            
            # Get user's teams based on role
            if user.role == UserRole.ADMIN:
                # Admins can see all teams
                user_teams = None  # Will be handled in the filter
            elif user.role == UserRole.MANAGER:
                # Managers can see teams from organizations they manage
                manager_orgs = Organization.objects.filter(
                    manager=user,
                    is_active=True
                ).values_list('id', flat=True)
                user_teams = Team.objects.filter(
                    organization__in=manager_orgs,
                    is_active=True
                ).values_list('id', flat=True)
            else:
                # Members can see teams they're members of
                user_teams = TeamMembers.objects.filter(
                    member=user,
                    is_active=True
                ).values_list('team', flat=True)
            
            # Check if user has access to any teams
            if user_teams is not None and not user_teams.exists():
                return create_not_found_error_response(
                    "You are not a member of any team.",
                    {"teams": []}
                )
            
            # Get schedules for the next 7 days
            today = timezone.now().date()
            next_week = today + timedelta(days=7)
            
            # Build the filter based on user role
            filter_kwargs = {
                'week_start_date__lte': next_week,
                'week_end_date__gte': today,
                'status': 'published'
            }
            
            if user_teams is not None:
                filter_kwargs['team__in'] = user_teams
            
            schedules = Schedule.objects.filter(
                **filter_kwargs
            ).select_related('team').prefetch_related('timeslots__assigned_member')
            
            serializer = WeeklyScheduleSerializer(schedules, many=True, context={'request': request})
            
            return create_success_response(
                "Team schedule retrieved successfully.",
                {"schedules": serializer.data}
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve team schedule. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=False, methods=['get'])
    def manager_team_schedule(self, request):
        """Get the full team schedule for managers - separate endpoint for better reliability."""
        try:
            user = request.user
            
            # Only allow managers and admins
            if user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
                return create_unauthorized_error_response(
                    "Only managers and admins can access this endpoint.",
                    {}
                )
            
            # Get manager's teams
            if user.role == UserRole.ADMIN:
                # Admins can see all teams
                user_teams = None
            else:
                # Managers can see teams from organizations they manage
                manager_orgs = Organization.objects.filter(
                    manager=user,
                    is_active=True
                ).values_list('id', flat=True)
                user_teams = Team.objects.filter(
                    organization__in=manager_orgs,
                    is_active=True
                ).values_list('id', flat=True)
            
            # Check if manager has access to any teams
            if user_teams is not None and not user_teams.exists():
                return create_not_found_error_response(
                    "You don't manage any teams.",
                    {"teams": []}
                )
            
            # Get schedules for the next 7 days
            today = timezone.now().date()
            next_week = today + timedelta(days=7)
            
            # Build the filter based on user role
            filter_kwargs = {
                'week_start_date__lte': next_week,
                'week_end_date__gte': today,
                'status': 'published'
            }
            
            if user_teams is not None:
                filter_kwargs['team__in'] = user_teams
            
            schedules = Schedule.objects.filter(
                **filter_kwargs
            ).select_related('team').prefetch_related('timeslots__assigned_member')
            
            serializer = WeeklyScheduleSerializer(schedules, many=True, context={'request': request})
            
            return create_success_response(
                "Manager team schedule retrieved successfully.",
                {"schedules": serializer.data}
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve manager team schedule. Please try again later.",
                {"original_error": str(e)}
            )


class SwapRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing swap requests."""
    
    permission_classes = [IsMemberOrManager]
    serializer_class = SwapRequestSerializer
    
    def get_queryset(self):
        """Get swap requests related to the current user."""
        user = self.request.user
        return SwapRequest.objects.filter(
            Q(requester=user) | Q(responder=user)
        ).select_related(
            'requester', 'responder', 'requester_slot__schedule__team',
            'responder_slot__schedule__team'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return SwapRequestCreateSerializer
        return SwapRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new swap request."""
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                swap_request = serializer.save()
                response_serializer = SwapRequestSerializer(swap_request, context={'request': request})
                
                return create_success_response(
                    "Swap request created successfully.",
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return create_validation_error_response(
                    "Please correct the errors below.",
                    serializer.errors
                )
                
        except Exception as e:
            return create_internal_error_response(
                "Failed to create swap request. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a swap request."""
        try:
            swap_request = self.get_object()
            
            # Check if the current user is the responder
            if swap_request.responder != request.user:
                return create_unauthorized_error_response(
                    "You can only accept swap requests sent to you.",
                    {"swap_request_id": pk}
                )
            
            # Check if the swap can be accepted
            if not swap_request.can_be_accepted():
                return create_validation_error_response(
                    "This swap request cannot be accepted at this time.",
                    {"reason": "Swap request is not valid or has expired"}
                )
            
            # Accept the swap
            if swap_request.accept():
                response_serializer = SwapRequestSerializer(swap_request, context={'request': request})
                return create_success_response(
                    "Swap request accepted and processed successfully.",
                    response_serializer.data
                )
            else:
                return create_internal_error_response(
                    "Failed to process the swap. Please try again later.",
                    {"swap_request_id": pk}
                )
                
        except SwapRequest.DoesNotExist:
            return create_not_found_error_response(
                "Swap request not found.",
                {"swap_request_id": pk}
            )
        except Exception as e:
            return create_internal_error_response(
                "Failed to accept swap request. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a swap request."""
        try:
            swap_request = self.get_object()
            
            # Check if the current user is the responder
            if swap_request.responder != request.user:
                return create_unauthorized_error_response(
                    "You can only reject swap requests sent to you.",
                    {"swap_request_id": pk}
                )
            
            # Check if the swap can be rejected
            if swap_request.status != 'pending':
                return create_validation_error_response(
                    "This swap request cannot be rejected.",
                    {"reason": "Swap request is not in pending status"}
                )
            
            # Get rejection reason from request data
            rejection_reason = request.data.get('rejection_reason', '')
            
            # Reject the swap
            swap_request.reject(rejection_reason)
            response_serializer = SwapRequestSerializer(swap_request, context={'request': request})
            
            return create_success_response(
                "Swap request rejected successfully.",
                response_serializer.data
            )
            
        except SwapRequest.DoesNotExist:
            return create_not_found_error_response(
                "Swap request not found.",
                {"swap_request_id": pk}
            )
        except Exception as e:
            return create_internal_error_response(
                "Failed to reject swap request. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get swap requests sent by the current user."""
        try:
            sent_requests = self.get_queryset().filter(requester=request.user)
            serializer = SwapRequestSerializer(sent_requests, many=True, context={'request': request})
            
            return create_success_response(
                "Sent swap requests retrieved successfully.",
                {"requests": serializer.data}
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve sent swap requests. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=False, methods=['get'])
    def received(self, request):
        """Get swap requests received by the current user."""
        try:
            received_requests = self.get_queryset().filter(responder=request.user)
            serializer = SwapRequestSerializer(received_requests, many=True, context={'request': request})
            
            return create_success_response(
                "Received swap requests retrieved successfully.",
                {"requests": serializer.data}
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve received swap requests. Please try again later.",
                {"original_error": str(e)}
            )


class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for team member information."""
    
    permission_classes = [IsMemberOrManager]
    serializer_class = TeamMemberSerializer
    
    def get_queryset(self):
        """Get team members for the current user's teams."""
        user = self.request.user
        
        # Get teams based on user role
        if user.role == UserRole.ADMIN:
            # Admins can see all team members
            return TeamMembers.objects.filter(
                is_active=True
            ).select_related('member').order_by('member__name')
        elif user.role == UserRole.MANAGER:
            # Managers can see members of teams from organizations they manage
            manager_orgs = Organization.objects.filter(
                manager=user,
                is_active=True
            ).values_list('id', flat=True)
            user_teams = Team.objects.filter(
                organization__in=manager_orgs,
                is_active=True
            ).values_list('id', flat=True)
        else:
            # Members can see members of teams they're part of
            user_teams = TeamMembers.objects.filter(
                member=user,
                is_active=True
            ).values_list('team', flat=True)
        
        return TeamMembers.objects.filter(
            team__in=user_teams,
            is_active=True
        ).select_related('member').order_by('member__name')
    
    def list(self, request):
        """Get all team members."""
        try:
            team_members = self.get_queryset()
            serializer = TeamMemberSerializer(team_members, many=True)
            
            return create_success_response(
                "Team members retrieved successfully.",
                {"members": serializer.data}
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve team members. Please try again later.",
                {"original_error": str(e)}
            )
    
    @action(detail=False, methods=['get'])
    def manager_team_members(self, request):
        """Get team members for managers - separate endpoint for better reliability."""
        try:
            user = request.user
            
            # Only allow managers and admins
            if user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
                return create_unauthorized_error_response(
                    "Only managers and admins can access this endpoint.",
                    {}
                )
            
            # Get team members based on user role
            if user.role == UserRole.ADMIN:
                # Admins can see all team members
                team_members = TeamMembers.objects.filter(
                    is_active=True
                ).select_related('member').order_by('member__name')
            else:
                # Managers can see members of teams from organizations they manage
                manager_orgs = Organization.objects.filter(
                    manager=user,
                    is_active=True
                ).values_list('id', flat=True)
                user_teams = Team.objects.filter(
                    organization__in=manager_orgs,
                    is_active=True
                ).values_list('id', flat=True)
                
                team_members = TeamMembers.objects.filter(
                    team__in=user_teams,
                    is_active=True
                ).select_related('member').order_by('member__name')
            
            serializer = TeamMemberSerializer(team_members, many=True)
            
            return create_success_response(
                "Manager team members retrieved successfully.",
                {"members": serializer.data}
            )
            
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve manager team members. Please try again later.",
                {"original_error": str(e)}
            )
