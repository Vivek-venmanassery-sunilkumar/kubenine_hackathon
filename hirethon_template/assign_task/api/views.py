from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import TeamScheduleConfig, Schedule, Timeslot, ScheduleValidation, SwapRequest
from .serializers import (
    TeamScheduleConfigSerializer, ScheduleSerializer, ScheduleCreateSerializer,
    TeamScheduleStatusSerializer, TimeslotSerializer, SwapRequestSerializer, SwapRequestCreateSerializer
)
from hirethon_template.manager_dashboard.models import Team
from hirethon_template.authentication.permissions import IsManagerOrAdmin
from ..tasks import generate_weekly_schedules, validate_all_draft_schedules, auto_publish_valid_schedules

User = get_user_model()


@api_view(['GET', 'POST'])
@permission_classes([IsManagerOrAdmin])
def team_schedule_config(request):
    """Get or create team schedule configuration."""
    if request.method == 'GET':
        team_id = request.query_params.get('team_id')
        if not team_id:
            return Response(
                {"error": "team_id parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            team = Team.objects.get(id=team_id)
            config, created = TeamScheduleConfig.objects.get_or_create(team=team)
            serializer = TeamScheduleConfigSerializer(config)
            return Response(serializer.data)
        except Team.DoesNotExist:
            return Response(
                {"error": "Team not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    elif request.method == 'POST':
        team_id = request.data.get('team')
        if not team_id:
            return Response(
                {"error": "team field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            team = Team.objects.get(id=team_id)
            # Get or create the config
            config, created = TeamScheduleConfig.objects.get_or_create(team=team)
            serializer = TeamScheduleConfigSerializer(config, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Team.DoesNotExist:
            return Response(
                {"error": "Team not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['PUT'])
@permission_classes([IsManagerOrAdmin])
def update_team_schedule_config(request, config_id):
    """Update team schedule configuration."""
    try:
        config = TeamScheduleConfig.objects.get(id=config_id)
        serializer = TeamScheduleConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except TeamScheduleConfig.DoesNotExist:
        return Response(
            {"error": "Configuration not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def team_schedule_status(request, team_id):
    """Get team schedule status and requirements."""
    try:
        team = Team.objects.get(id=team_id)
        print(f"DEBUG: Getting schedule status for team {team.team_name} (ID: {team_id})")
        
        # Check member count directly
        member_count = team.members.filter(is_active=True).count()
        print(f"DEBUG: Direct member count query: {member_count}")
        
        config, created = TeamScheduleConfig.objects.get_or_create(team=team)
        print(f"DEBUG: Config created: {created}, timeslot_duration: {config.timeslot_duration_hours}")
        
        serializer = TeamScheduleStatusSerializer(config)
        print(f"DEBUG: Serialized data: {serializer.data}")
        return Response(serializer.data)
    except Team.DoesNotExist:
        print(f"DEBUG: Team with ID {team_id} not found")
        return Response(
            {"error": "Team not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsManagerOrAdmin])
def generate_schedule(request, team_id):
    """Generate a weekly schedule for a team."""
    try:
        team = Team.objects.get(id=team_id)
        config = TeamScheduleConfig.objects.get(team=team)
        
        # Check if team has enough members
        member_count = team.members.filter(is_active=True).count()
        required_members = calculate_required_members(config)
        
        if member_count < required_members:
            return Response(
                {
                    "error": f"Insufficient members. Need {required_members} members, have {member_count}",
                    "required_members": required_members,
                    "current_members": member_count
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get week start date from request or default to current week
        week_start_str = request.data.get('week_start_date')
        if week_start_str:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        else:
            # Default to current week's Monday
            today = timezone.now().date()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
        
        # Check if schedule already exists for this week
        existing_schedule = Schedule.objects.filter(
            team=team, 
            week_start_date=week_start
        ).first()
        
        if existing_schedule:
            return Response(
                {"error": "Schedule already exists for this week"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the schedule
        schedule = Schedule.objects.create(
            team=team,
            week_start_date=week_start,
            status='draft'
        )
        
        # Generate timeslots
        generate_timeslots(schedule, config)
        
        # Validate the schedule
        validate_schedule(schedule)
        
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Team.DoesNotExist:
        return Response(
            {"error": "Team not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except TeamScheduleConfig.DoesNotExist:
        return Response(
            {"error": "Team schedule configuration not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team_schedules(request, team_id):
    """Get all schedules for a team."""
    try:
        team = Team.objects.get(id=team_id)
        schedules = Schedule.objects.filter(team=team).order_by('-week_start_date')
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    except Team.DoesNotExist:
        return Response(
            {"error": "Team not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def schedule_detail(request, schedule_id):
    """Get detailed information about a specific schedule."""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data)
    except Schedule.DoesNotExist:
        return Response(
            {"error": "Schedule not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsManagerOrAdmin])
def publish_schedule(request, schedule_id):
    """Publish a draft schedule."""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        if schedule.status != 'draft':
            return Response(
                {"error": "Only draft schedules can be published"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate before publishing
        validation = validate_schedule(schedule)
        if not validation.is_valid:
            return Response(
                {
                    "error": "Schedule validation failed",
                    "validation_errors": validation.validation_errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedule.status = 'published'
        schedule.save()
        
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data)
        
    except Schedule.DoesNotExist:
        return Response(
            {"error": "Schedule not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsManagerOrAdmin])
def validate_schedule_endpoint(request, schedule_id):
    """Validate a schedule without publishing it."""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        validation = validate_schedule(schedule)
        
        return Response({
            "is_valid": validation.is_valid,
            "validation_errors": validation.validation_errors,
            "schedule_id": schedule_id
        })
        
    except Schedule.DoesNotExist:
        return Response(
            {"error": "Schedule not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


def calculate_required_members(config):
    """Get minimum number of members needed to start scheduling."""
    return config.get_min_team_size_for_scheduling()


def generate_timeslots(schedule, config):
    """Generate timeslots for a schedule based on configuration."""
    week_start = schedule.week_start_date
    timeslot_duration = timedelta(hours=config.timeslot_duration_hours)
    min_break = timedelta(hours=config.min_break_hours)
    
    # Generate timeslots for the entire week (7 days)
    current_datetime = timezone.make_aware(
        datetime.combine(week_start, datetime.min.time())
    )
    week_end = current_datetime + timedelta(days=7)
    
    timeslots = []
    while current_datetime < week_end:
        end_datetime = current_datetime + timeslot_duration
        
        # Create timeslot
        timeslot = Timeslot.objects.create(
            schedule=schedule,
            start_datetime=current_datetime,
            end_datetime=end_datetime,
            is_break=False
        )
        timeslots.append(timeslot)
        
        # Move to next timeslot with minimum break
        current_datetime = end_datetime + min_break
    
    # Assign members to timeslots using round-robin
    assign_members_to_timeslots(schedule, timeslots)


def assign_members_to_timeslots(schedule, timeslots):
    """Assign team members to timeslots using round-robin algorithm."""
    team = schedule.team
    active_members = list(team.members.filter(is_active=True).values_list('member', flat=True))
    
    if not active_members:
        return
    
    # Track member hours for constraint checking
    member_hours = {member_id: 0 for member_id in active_members}
    max_daily_hours = 8  # Fixed constraint
    max_weekly_hours = 40  # Fixed constraint
    
    member_index = 0
    for timeslot in timeslots:
        if timeslot.is_break:
            continue
        
        # Find next available member
        attempts = 0
        while attempts < len(active_members):
            member_id = active_members[member_index]
            
            # Check if member can take this timeslot
            timeslot_hours = timeslot.duration_hours
            if (member_hours[member_id] + timeslot_hours <= max_weekly_hours):
                # Check daily hours constraint
                member_daily_hours = get_member_daily_hours(member_id, timeslot.start_datetime.date())
                if member_daily_hours + timeslot_hours <= max_daily_hours:
                    timeslot.assigned_member_id = member_id
                    timeslot.save()
                    member_hours[member_id] += timeslot_hours
                    break
            
            member_index = (member_index + 1) % len(active_members)
            attempts += 1
        
        member_index = (member_index + 1) % len(active_members)


def get_member_daily_hours(member_id, date):
    """Get total hours assigned to a member on a specific date."""
    start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
    end_of_day = start_of_day + timedelta(days=1)
    
    timeslots = Timeslot.objects.filter(
        assigned_member_id=member_id,
        start_datetime__gte=start_of_day,
        start_datetime__lt=end_of_day,
        is_break=False
    )
    
    return sum(timeslot.duration_hours for timeslot in timeslots)


def validate_schedule(schedule):
    """Validate a schedule and create validation record."""
    validation, created = ScheduleValidation.objects.get_or_create(schedule=schedule)
    
    errors = []
    warnings = []
    
    # Check if all timeslots are assigned
    unassigned_timeslots = schedule.timeslots.filter(
        assigned_member__isnull=True, 
        is_break=False
    ).count()
    
    if unassigned_timeslots > 0:
        errors.append(f"{unassigned_timeslots} timeslots are unassigned")
    
    # Check member hour constraints
    for member in schedule.team.members.filter(is_active=True):
        member_timeslots = schedule.timeslots.filter(
            assigned_member=member.member,
            is_break=False
        )
        
        total_hours = sum(ts.duration_hours for ts in member_timeslots)
        if total_hours > 40:  # Fixed constraint
            errors.append(f"Member {member.member.name} exceeds 40 hours per week ({total_hours}h)")
        
        # Check daily hours
        daily_hours = {}
        for ts in member_timeslots:
            date = ts.start_datetime.date()
            daily_hours[date] = daily_hours.get(date, 0) + ts.duration_hours
        
        for date, hours in daily_hours.items():
            if hours > 8:  # Fixed constraint
                errors.append(f"Member {member.member.name} exceeds 8 hours on {date} ({hours}h)")
    
    # Check if team has sufficient members
    member_count = schedule.team.members.filter(is_active=True).count()
    required_members = schedule.team.schedule_config.get_min_team_size_for_scheduling()
    validation.has_sufficient_members = member_count >= required_members
    
    if not validation.has_sufficient_members:
        errors.append(f"Insufficient members: need {required_members}, have {member_count}")
    
    validation.validation_errors = errors
    validation.validation_warnings = warnings
    validation.is_valid = len(errors) == 0
    validation.save()
    
    return validation


@api_view(['POST'])
@permission_classes([IsManagerOrAdmin])
def trigger_automatic_scheduling(request):
    """Manually trigger automatic scheduling tasks."""
    task_type = request.data.get('task_type', 'all')
    
    if task_type == 'generate' or task_type == 'all':
        result = generate_weekly_schedules.delay()
        return Response({
            'message': 'Weekly schedule generation task queued',
            'task_id': result.id
        }, status=status.HTTP_202_ACCEPTED)
    
    elif task_type == 'validate' or task_type == 'all':
        result = validate_all_draft_schedules.delay()
        return Response({
            'message': 'Schedule validation task queued',
            'task_id': result.id
        }, status=status.HTTP_202_ACCEPTED)
    
    elif task_type == 'publish' or task_type == 'all':
        result = auto_publish_valid_schedules.delay()
        return Response({
            'message': 'Auto-publish schedules task queued',
            'task_id': result.id
        }, status=status.HTTP_202_ACCEPTED)
    
    else:
        return Response(
            {'error': 'Invalid task_type. Must be: generate, validate, publish, or all'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def scheduling_status(request):
    """Get status of automatic scheduling system."""
    from django_celery_beat.models import PeriodicTask
    
    # Get current week's Monday
    today = timezone.now().date()
    days_since_monday = today.weekday()
    current_week_monday = today - timedelta(days=days_since_monday)
    next_week_monday = current_week_monday + timedelta(days=7)
    
    # Count schedules
    current_week_schedules = Schedule.objects.filter(week_start_date=current_week_monday).count()
    next_week_schedules = Schedule.objects.filter(week_start_date=next_week_monday).count()
    
    # Count teams with configs
    teams_with_configs = Team.objects.filter(schedule_config__isnull=False).count()
    
    # Get periodic task status
    periodic_tasks = PeriodicTask.objects.filter(
        name__in=[
            'generate-weekly-schedules',
            'validate-draft-schedules', 
            'auto-publish-schedules'
        ]
    )
    
    task_status = {}
    for task in periodic_tasks:
        task_status[task.name] = {
            'enabled': task.enabled,
            'last_run_at': task.last_run_at,
            'next_run_time': task.next_run_time
        }
    
    return Response({
        'current_week': {
            'monday': current_week_monday,
            'schedules_count': current_week_schedules
        },
        'next_week': {
            'monday': next_week_monday,
            'schedules_count': next_week_schedules
        },
        'teams_with_configs': teams_with_configs,
        'periodic_tasks': task_status,
        'system_status': 'active' if all(task.enabled for task in periodic_tasks) else 'inactive'
    })


# Swap Request API Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_swap_request(request):
    """Create a new swap request."""
    try:
        # Set the requester to the current user
        data = request.data.copy()
        data['requester'] = request.user.id
        
        serializer = SwapRequestCreateSerializer(data=data)
        if serializer.is_valid():
            swap_request = serializer.save()
            response_serializer = SwapRequestSerializer(swap_request)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_swap_requests(request):
    """Get swap requests for the current user."""
    try:
        # Get requests sent by the user
        sent_requests = SwapRequest.objects.filter(requester=request.user)
        
        # Get requests received by the user
        received_requests = SwapRequest.objects.filter(responder=request.user)
        
        # Get all requests for the user's team
        from hirethon_template.manager_dashboard.models import TeamMembers
        user_teams = TeamMembers.objects.filter(
            member=request.user, is_active=True
        ).values_list('team', flat=True)
        
        team_requests = SwapRequest.objects.filter(
            requester_slot__schedule__team__in=user_teams
        ).exclude(requester=request.user).exclude(responder=request.user)
        
        # Serialize all requests
        sent_data = SwapRequestSerializer(sent_requests, many=True).data
        received_data = SwapRequestSerializer(received_requests, many=True).data
        team_data = SwapRequestSerializer(team_requests, many=True).data
        
        return Response({
            'sent_requests': sent_data,
            'received_requests': received_data,
            'team_requests': team_data
        })
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_swap_request(request, swap_id):
    """Accept a swap request."""
    try:
        swap_request = SwapRequest.objects.get(id=swap_id, responder=request.user)
        
        if not swap_request.can_be_accepted():
            return Response(
                {"error": "This swap request cannot be accepted"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Accept and process the swap
        if swap_request.accept():
            serializer = SwapRequestSerializer(swap_request)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "Failed to process the swap"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except SwapRequest.DoesNotExist:
        return Response(
            {"error": "Swap request not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_swap_request(request, swap_id):
    """Reject a swap request."""
    try:
        swap_request = SwapRequest.objects.get(id=swap_id, responder=request.user)
        
        if swap_request.status != 'pending':
            return Response(
                {"error": "This swap request cannot be rejected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        swap_request.reject(reason)
        
        serializer = SwapRequestSerializer(swap_request)
        return Response(serializer.data)
    except SwapRequest.DoesNotExist:
        return Response(
            {"error": "Swap request not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_team_schedule_for_swapping(request, team_id):
    """Get team schedule for swapping (shows all members' slots)."""
    try:
        # Verify user is a member of this team
        from hirethon_template.manager_dashboard.models import TeamMembers
        if not TeamMembers.objects.filter(
            team_id=team_id, member=request.user, is_active=True
        ).exists():
            return Response(
                {"error": "You are not a member of this team"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get current week's schedule
        today = timezone.now().date()
        days_since_monday = today.weekday()
        current_week_monday = today - timedelta(days=days_since_monday)
        
        try:
            schedule = Schedule.objects.get(
                team_id=team_id,
                week_start_date=current_week_monday
            )
            
            # Get all timeslots with member details
            timeslots = schedule.timeslots.filter(is_break=False).select_related('assigned_member')
            
            # Group by member
            member_slots = {}
            for timeslot in timeslots:
                if timeslot.assigned_member:
                    member_id = timeslot.assigned_member.id
                    if member_id not in member_slots:
                        member_slots[member_id] = {
                            'member_id': member_id,
                            'member_name': timeslot.assigned_member.name,
                            'slots': []
                        }
                    
                    member_slots[member_id]['slots'].append({
                        'id': timeslot.id,
                        'start_datetime': timeslot.start_datetime,
                        'end_datetime': timeslot.end_datetime,
                        'duration_hours': timeslot.duration_hours,
                        'is_my_slot': timeslot.assigned_member == request.user
                    })
            
            return Response({
                'schedule_id': schedule.id,
                'week_start_date': schedule.week_start_date,
                'week_end_date': schedule.week_end_date,
                'member_slots': list(member_slots.values())
            })
            
        except Schedule.DoesNotExist:
            return Response(
                {"error": "No schedule found for this team"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


