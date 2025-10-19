#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from hirethon_template.assign_task.tasks import generate_weekly_schedules
from hirethon_template.assign_task.models import Schedule, Timeslot
from hirethon_template.manager_dashboard.models import Team

print('=== TESTING SCHEDULE GENERATION ===')

# Check current state
print(f'Before generation:')
print(f'  Schedules: {Schedule.objects.count()}')
print(f'  Timeslots: {Timeslot.objects.count()}')

try:
    result = generate_weekly_schedules()
    print('Schedule generation result:')
    print(f'Generated schedules: {len(result["generated_schedules"])}')
    print(f'Failed teams: {len(result["failed_teams"])}')
    print(f'Total teams processed: {result["total_teams_processed"]}')
    
    if result['generated_schedules']:
        for schedule_info in result['generated_schedules']:
            print(f'  - {schedule_info["team"]}: Schedule ID {schedule_info["schedule_id"]}')
    
    if result['failed_teams']:
        for failed in result['failed_teams']:
            print(f'  - FAILED {failed["team"]}: {failed["reason"]}')
    
    print(f'After generation:')
    print(f'  Schedules: {Schedule.objects.count()}')
    print(f'  Timeslots: {Timeslot.objects.count()}')
    
    if Schedule.objects.exists():
        schedule = Schedule.objects.first()
        print(f'First schedule: {schedule.team.team_name} - {schedule.week_start_date}')
        print(f'  Timeslots: {schedule.timeslots.count()}')
        print(f'  Assigned: {schedule.timeslots.filter(assigned_member__isnull=False).count()}')
        print(f'  Unassigned: {schedule.timeslots.filter(assigned_member__isnull=True).count()}')
        
        # Show first few timeslots
        for i, timeslot in enumerate(schedule.timeslots.all()[:5]):
            member = timeslot.assigned_member.name if timeslot.assigned_member else 'None'
            print(f'    {i+1}. {timeslot.start_datetime} - {timeslot.end_datetime} -> {member}')

except Exception as e:
    print(f'ERROR during schedule generation: {e}')
    import traceback
    traceback.print_exc()
