from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from .models import TeamScheduleConfig, Schedule
from hirethon_template.manager_dashboard.models import Team


@shared_task
def generate_weekly_schedules():
    """
    Automatically generate weekly schedules for all teams.
    This task should run every Sunday to generate next week's schedules.
    """
    from .api.views import generate_timeslots, assign_members_to_timeslots, validate_schedule
    
    # Get next week's Monday
    today = timezone.now().date()
    days_since_monday = today.weekday()
    current_week_monday = today - timedelta(days=days_since_monday)
    next_week_monday = current_week_monday + timedelta(days=7)
    
    generated_schedules = []
    failed_teams = []
    
    # Get all active teams and ensure they have schedule configurations
    all_teams = Team.objects.filter(is_active=True)
    teams_with_configs = []
    
    for team in all_teams:
        # Create config if it doesn't exist
        from .models import TeamScheduleConfig
        config, created = TeamScheduleConfig.objects.get_or_create(team=team)
        if created:
            print(f"Created schedule config for team {team.team_name}")
        teams_with_configs.append(team)
    
    for team in teams_with_configs:
        try:
            # Check if schedule already exists for next week
            existing_schedule = Schedule.objects.filter(
                team=team,
                week_start_date=next_week_monday
            ).first()
            
            if existing_schedule:
                print(f"Schedule already exists for team {team.team_name} for week {next_week_monday}")
                continue
            
            # Check if team has enough members
            config = team.schedule_config
            member_count = team.members.filter(is_active=True).count()
            required_members = calculate_required_members(config)
            
            if member_count < required_members:
                failed_teams.append({
                    'team': team.team_name,
                    'reason': f'Insufficient members: need {required_members}, have {member_count}'
                })
                continue
            
            # Create the schedule (published immediately)
            schedule = Schedule.objects.create(
                team=team,
                week_start_date=next_week_monday,
                status='published'
            )
            
            # Generate timeslots
            generate_timeslots(schedule, config)
            
            # Validate the schedule
            validate_schedule(schedule)
            
            generated_schedules.append({
                'team': team.team_name,
                'schedule_id': schedule.id,
                'week_start': next_week_monday
            })
            
            print(f"Generated schedule for team {team.team_name}")
            
        except Exception as e:
            failed_teams.append({
                'team': team.team_name,
                'reason': str(e)
            })
            print(f"Failed to generate schedule for team {team.team_name}: {str(e)}")
    
    return {
        'generated_schedules': generated_schedules,
        'failed_teams': failed_teams,
        'total_teams_processed': len(teams_with_configs)
    }


@shared_task
def validate_all_draft_schedules():
    """
    Validate all draft schedules and notify managers of any issues.
    This task should run daily to check for validation issues.
    """
    from .api.views import validate_schedule
    
    draft_schedules = Schedule.objects.filter(status='draft')
    validation_results = []
    
    for schedule in draft_schedules:
        try:
            validation = validate_schedule(schedule)
            validation_results.append({
                'schedule_id': schedule.id,
                'team': schedule.team.team_name,
                'is_valid': validation.is_valid,
                'errors': validation.validation_errors,
                'warnings': validation.validation_warnings
            })
        except Exception as e:
            validation_results.append({
                'schedule_id': schedule.id,
                'team': schedule.team.team_name,
                'error': str(e)
            })
    
    return validation_results


@shared_task
def auto_publish_valid_schedules():
    """
    Automatically publish schedules that are valid and ready.
    This task should run on Monday morning to publish the current week's schedules.
    """
    # Get current week's Monday
    today = timezone.now().date()
    days_since_monday = today.weekday()
    current_week_monday = today - timedelta(days=days_since_monday)
    
    # Find valid draft schedules for current week
    valid_schedules = Schedule.objects.filter(
        week_start_date=current_week_monday,
        status='draft',
        validation__is_valid=True
    )
    
    published_schedules = []
    
    for schedule in valid_schedules:
        try:
            schedule.status = 'published'
            schedule.save()
            published_schedules.append({
                'schedule_id': schedule.id,
                'team': schedule.team.team_name
            })
            print(f"Auto-published schedule for team {schedule.team.team_name}")
        except Exception as e:
            print(f"Failed to auto-publish schedule for team {schedule.team.team_name}: {str(e)}")
    
    return published_schedules


def calculate_required_members(config):
    """Calculate minimum number of members needed for 24/7 coverage."""
    hours_per_day = 24
    days_per_week = 7
    total_hours_per_week = hours_per_day * days_per_week
    max_hours_per_member = 40  # MAX_WEEKLY_HOURS
    
    required_members = (total_hours_per_week + max_hours_per_member - 1) // max_hours_per_member
    return required_members


# Helper functions moved from views.py to avoid circular imports
def generate_timeslots(schedule, config):
    """Generate timeslots for a schedule based on configuration."""
    from .models import Timeslot
    
    week_start = schedule.week_start_date
    timeslot_duration = timedelta(hours=config.timeslot_duration_hours)
    min_break = timedelta(hours=config.min_break_hours)
    
    # Generate timeslots for the entire week (7 days) with 24/7 coverage
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
        
        # Move to next timeslot immediately (no gap for 24/7 coverage)
        current_datetime = end_datetime
    
    # Assign members to timeslots using round-robin
    assign_members_to_timeslots(schedule, timeslots)


def assign_members_to_timeslots(schedule, timeslots):
    """Assign team members to timeslots using round-robin algorithm with rolling weekly tracking."""
    from .models import Timeslot, MemberWeeklyHours
    
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
    from .models import Timeslot
    
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
    from .models import ScheduleValidation, MemberWeeklyHours
    
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
    required_members = calculate_required_members(schedule.team.schedule_config)
    validation.has_sufficient_members = member_count >= required_members
    
    if not validation.has_sufficient_members:
        errors.append(f"Insufficient members: need {required_members}, have {member_count}")
    
    validation.validation_errors = errors
    validation.validation_warnings = warnings
    validation.is_valid = len(errors) == 0
    validation.save()
    
    return validation
