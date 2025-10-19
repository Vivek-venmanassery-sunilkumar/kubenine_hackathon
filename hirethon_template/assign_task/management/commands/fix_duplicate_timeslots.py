from django.core.management.base import BaseCommand
from hirethon_template.assign_task.models import Schedule, Timeslot
from hirethon_template.manager_dashboard.models import Team


class Command(BaseCommand):
    help = 'Fix duplicate timeslots in schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--team-id',
            type=int,
            help='Team ID to fix (if not provided, fixes all teams)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        team_id = options.get('team_id')
        dry_run = options.get('dry_run')
        
        if team_id:
            teams = Team.objects.filter(id=team_id)
        else:
            teams = Team.objects.filter(is_active=True)
        
        total_duplicates_removed = 0
        
        for team in teams:
            self.stdout.write(f'Processing team: {team.team_name}')
            
            for schedule in team.schedules.all():
                self.stdout.write(f'  Schedule {schedule.id} (Week {schedule.week_start_date})')
                
                # Get all timeslots for this schedule
                timeslots = schedule.timeslots.all().order_by('start_datetime')
                self.stdout.write(f'    Total timeslots: {timeslots.count()}')
                
                # Track seen time ranges
                seen_ranges = set()
                duplicates_to_remove = []
                
                for timeslot in timeslots:
                    time_range = f"{timeslot.start_datetime} - {timeslot.end_datetime}"
                    
                    if time_range in seen_ranges:
                        # This is a duplicate
                        duplicates_to_remove.append(timeslot.id)
                        self.stdout.write(f'    DUPLICATE: {time_range} (ID: {timeslot.id})')
                    else:
                        seen_ranges.add(time_range)
                
                # Remove duplicates
                if duplicates_to_remove:
                    if dry_run:
                        self.stdout.write(f'    Would remove {len(duplicates_to_remove)} duplicate timeslots')
                    else:
                        Timeslot.objects.filter(id__in=duplicates_to_remove).delete()
                        total_duplicates_removed += len(duplicates_to_remove)
                        self.stdout.write(f'    Removed {len(duplicates_to_remove)} duplicate timeslots')
                else:
                    self.stdout.write(f'    No duplicates found')
                
                # Show final count
                final_count = schedule.timeslots.count()
                self.stdout.write(f'    Final timeslots: {final_count}')
        
        if dry_run:
            self.stdout.write(f'\\nDRY RUN: Would remove {total_duplicates_removed} duplicate timeslots')
        else:
            self.stdout.write(f'\\nSuccessfully removed {total_duplicates_removed} duplicate timeslots')
