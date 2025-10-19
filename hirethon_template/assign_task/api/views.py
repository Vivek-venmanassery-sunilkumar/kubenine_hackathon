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
    """Generate timeslots for 24/7 coverage with 8-hour max per member per day."""
    week_start = schedule.week_start_date
    max_slot_duration = config.timeslot_duration_hours  # Maximum hours per slot
    min_break_hours = config.min_break_hours
    
    # Generate hourly timeslots for 24/7 coverage (168 hours total)
    current_datetime = timezone.make_aware(
        datetime.combine(week_start, datetime.min.time())
    )
    week_end = current_datetime + timedelta(days=7)
    
    timeslots = []
    hour_count = 0
    
    # Generate 1-hour timeslots for the entire week
    while current_datetime < week_end:
        end_datetime = current_datetime + timedelta(hours=1)
        
        # Create hourly timeslot
        timeslot = Timeslot.objects.create(
            schedule=schedule,
            start_datetime=current_datetime,
            end_datetime=end_datetime,
            is_break=False
        )
        timeslots.append(timeslot)
        
        current_datetime = end_datetime
        hour_count += 1
    
    # Group timeslots by day for member assignment
    daily_timeslots = {}
    for timeslot in timeslots:
        day = timeslot.start_datetime.date()
        if day not in daily_timeslots:
            daily_timeslots[day] = []
        daily_timeslots[day].append(timeslot)
    
    # Assign members to timeslots with 8-hour daily limit
    assign_members_with_daily_limits(schedule, daily_timeslots, max_slot_duration, min_break_hours)


def assign_members_with_daily_limits(schedule, daily_timeslots, max_slot_duration, min_break_hours):
    """Assign members to timeslots ensuring 24/7 coverage with 8-hour daily limits."""
    team = schedule.team
    active_members = list(team.members.filter(is_active=True).values_list('member', flat=True))
    
    if not active_members:
        return
    
    # Process each day separately
    for day, day_timeslots in daily_timeslots.items():
        # Track daily hours for each member
        daily_member_hours = {member_id: 0 for member_id in active_members}
        weekly_member_hours = {member_id: 0 for member_id in active_members}  # Track weekly hours
        
        # Sort timeslots by start time
        day_timeslots.sort(key=lambda x: x.start_datetime)
        
        # Assign members to each hour of the day
        member_index = 0
        for timeslot in day_timeslots:
            # Find next available member for this hour
            attempts = 0
            assigned = False
            
            while attempts < len(active_members) and not assigned:
                member_id = active_members[member_index]
                
                # Check constraints
                can_assign = (
                    daily_member_hours[member_id] < 8 and  # Daily 8-hour limit
                    weekly_member_hours[member_id] < 40  # Weekly 40-hour limit
                )
                
                if can_assign:
                    # Assign member to this hour
                    timeslot.assigned_member_id = member_id
                    timeslot.save()
                    
                    # Update tracking
                    daily_member_hours[member_id] += 1
                    weekly_member_hours[member_id] += 1
                    
                    assigned = True
                
                member_index = (member_index + 1) % len(active_members)
                attempts += 1
            
            # If no member could be assigned, assign to the first available member (emergency)
            if not assigned:
                member_id = active_members[0]
                timeslot.assigned_member_id = member_id
                timeslot.save()
                print(f"WARNING: Emergency assignment for {timeslot.start_datetime} - member {member_id}")


def has_sufficient_break(member_id, current_time, day_timeslots, min_break_hours):
    """Check if member had sufficient break since last assignment."""
    # Find the last timeslot assigned to this member on the same day
    last_assignment = None
    for timeslot in day_timeslots:
        if (timeslot.assigned_member_id == member_id and 
            timeslot.start_datetime < current_time):
            if last_assignment is None or timeslot.start_datetime > last_assignment.start_datetime:
                last_assignment = timeslot
    
    if last_assignment is None:
        return True  # No previous assignment today
    
    # Check if enough time has passed
    time_since_last = current_time - last_assignment.end_datetime
    return time_since_last >= timedelta(hours=min_break_hours)


def assign_members_to_timeslots(schedule, timeslots):
    """Assign team members to timeslots using round-robin algorithm with rolling weekly tracking."""
    from .models import MemberWeeklyHours
    
    team = schedule.team
    active_members = list(team.members.filter(is_active=True).values_list('member', flat=True))
    
    if not active_members:
        return
    
    # Get week start date (Monday)
    week_start = schedule.week_start_date
    
    # Track member hours for constraint checking
    member_hours = {member_id: 0 for member_id in active_members}
    max_daily_hours = 8  # Fixed constraint
    
    # Get or create weekly hour records for all members
    weekly_records = {}
    for member_id in active_members:
        weekly_record, created = MemberWeeklyHours.objects.get_or_create(
            member_id=member_id,
            team=team,
            week_start_date=week_start,
            defaults={
                'base_weekly_limit': 40,
                'adjusted_weekly_limit': 40,
                'scheduled_hours': 0,
                'actual_hours': 0
            }
        )
        weekly_records[member_id] = weekly_record
    
    member_index = 0
    for timeslot in timeslots:
        if timeslot.is_break:
            continue
        
        # Find next available member
        attempts = 0
        while attempts < len(active_members):
            member_id = active_members[member_index]
            weekly_record = weekly_records[member_id]
            
            # Check if member can take this timeslot
            timeslot_hours = timeslot.duration_hours
            
            # Check daily hours constraint (always enforced)
            member_daily_hours = get_member_daily_hours(member_id, timeslot.start_datetime.date())
            if member_daily_hours + timeslot_hours <= max_daily_hours:
                # Check weekly hours constraint (flexible with overage tracking)
                current_weekly_hours = member_hours[member_id]
                
                # Allow assignment if:
                # 1. Within adjusted weekly limit, OR
                # 2. Weekend scheduling (Saturday/Sunday) and no other options
                is_weekend = timeslot.start_datetime.weekday() >= 5  # Saturday=5, Sunday=6
                within_weekly_limit = current_weekly_hours + timeslot_hours <= weekly_record.adjusted_weekly_limit
                
                # Weekend override: allow up to 8 hours over the base limit on weekends
                is_weekend_override = is_weekend and current_weekly_hours + timeslot_hours <= weekly_record.base_weekly_limit + 8
                
                # Emergency override: if no one else can take the slot and it's critical
                is_emergency_override = current_weekly_hours + timeslot_hours <= weekly_record.base_weekly_limit + 12  # Max 12 hours overage
                
                if within_weekly_limit or is_weekend_override or is_emergency_override:
                    timeslot.assigned_member_id = member_id
                    timeslot.save()
                    member_hours[member_id] += timeslot_hours
                    
                    # Update weekly record
                    weekly_record.scheduled_hours += timeslot_hours
                    weekly_record.actual_hours += timeslot_hours
                    if is_weekend_override and not within_weekly_limit:
                        weekly_record.is_weekend_override = True
                        weekly_record.notes = f"Weekend scheduling required {timeslot_hours}h overage"
                    weekly_record.save()
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
    """Validate a schedule and create validation record with flexible weekly limits."""
    from .models import MemberWeeklyHours
    
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
    
    # Check member hour constraints with flexible weekly limits
    for member in schedule.team.members.filter(is_active=True):
        member_timeslots = schedule.timeslots.filter(
            assigned_member=member.member,
            is_break=False
        )
        
        total_hours = sum(ts.duration_hours for ts in member_timeslots)
        
        # Get weekly record for this member
        weekly_record = MemberWeeklyHours.objects.filter(
            member=member.member,
            team=schedule.team,
            week_start_date=schedule.week_start_date
        ).first()
        
        if weekly_record:
            # Check against adjusted weekly limit
            if total_hours > weekly_record.adjusted_weekly_limit:
                if weekly_record.is_weekend_override:
                    warnings.append(f"Member {member.member.name} has weekend override: {total_hours}h (limit: {weekly_record.adjusted_weekly_limit}h)")
                else:
                    errors.append(f"Member {member.member.name} exceeds adjusted weekly limit: {total_hours}h (limit: {weekly_record.adjusted_weekly_limit}h)")
            
            # Check for significant overage (more than 8 hours over base limit)
            if total_hours > weekly_record.base_weekly_limit + 8:
                errors.append(f"Member {member.member.name} has excessive overage: {total_hours}h (base limit: {weekly_record.base_weekly_limit}h)")
        else:
            # Fallback to base limit if no weekly record
            if total_hours > 40:
                errors.append(f"Member {member.member.name} exceeds base weekly limit: {total_hours}h (limit: 40h)")
        
        # Check daily hours (always enforced)
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


@api_view(['POST'])
@permission_classes([IsManagerOrAdmin])
def regenerate_team_schedules(request, team_id):
    """Manually regenerate schedules for a team from a specific date onwards."""
    try:
        team = Team.objects.get(id=team_id)
        
        # Get from_date from request or default to tomorrow
        from_date_str = request.data.get('from_date')
        if from_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        else:
            from_date = timezone.now().date() + timedelta(days=1)
        
        # Trigger the regeneration task
        from .tasks import regenerate_schedules_for_team
        result = regenerate_schedules_for_team.delay(team_id, from_date)
        
        return Response({
            'message': 'Schedule regeneration task queued',
            'task_id': result.id,
            'team_name': team.team_name,
            'from_date': from_date
        }, status=status.HTTP_202_ACCEPTED)
        
    except Team.DoesNotExist:
        return Response(
            {"error": "Team not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsManagerOrAdmin])
def check_team_auto_scheduling(request, team_id):
    """Check if team should start auto-scheduling and trigger if needed."""
    try:
        team = Team.objects.get(id=team_id)
        
        # Trigger the check task
        from .tasks import check_and_start_auto_scheduling
        result = check_and_start_auto_scheduling.delay(team_id)
        
        return Response({
            'message': 'Auto-scheduling check task queued',
            'task_id': result.id,
            'team_name': team.team_name
        }, status=status.HTTP_202_ACCEPTED)
        
    except Team.DoesNotExist:
        return Response(
            {"error": "Team not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def team_member_status(request, team_id):
    """Get team member status and scheduling readiness."""
    try:
        team = Team.objects.get(id=team_id)
        member_count = team.members.filter(is_active=True).count()
        required_members = 5  # Minimum required for scheduling
        
        # Check if team has any schedules
        has_schedules = Schedule.objects.filter(team=team).exists()
        
        # Get current week's schedule if exists
        today = timezone.now().date()
        days_since_monday = today.weekday()
        current_week_monday = today - timedelta(days=days_since_monday)
        
        current_schedule = None
        try:
            current_schedule = Schedule.objects.get(
                team=team,
                week_start_date=current_week_monday
            )
        except Schedule.DoesNotExist:
            pass
        
        return Response({
            'team_name': team.team_name,
            'member_count': member_count,
            'required_members': required_members,
            'can_schedule': member_count >= required_members,
            'has_schedules': has_schedules,
            'current_schedule': {
                'exists': current_schedule is not None,
                'timeslots_count': current_schedule.timeslots.count() if current_schedule else 0,
                'assigned_count': current_schedule.timeslots.filter(assigned_member__isnull=False).count() if current_schedule else 0
            } if current_schedule else None
        })
        
    except Team.DoesNotExist:
        return Response(
            {"error": "Team not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsManagerOrAdmin])
def cleanup_duplicate_timeslots(request, team_id=None):
    """Clean up duplicate timeslots for a team."""
    try:
        from .tasks import cleanup_duplicate_timeslots
        
        # Trigger the cleanup task
        result = cleanup_duplicate_timeslots.delay(team_id)
        
        return Response({
            'message': 'Duplicate cleanup task queued',
            'task_id': result.id,
            'team_id': team_id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


