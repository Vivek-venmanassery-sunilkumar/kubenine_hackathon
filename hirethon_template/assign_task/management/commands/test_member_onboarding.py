from django.core.management.base import BaseCommand
from hirethon_template.manager_dashboard.models import Team, TeamMembers
from hirethon_template.assign_task.tasks import check_and_start_auto_scheduling, regenerate_schedules_for_team
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Test member onboarding and schedule regeneration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--team-id',
            type=int,
            help='Team ID to test with'
        )
        parser.add_argument(
            '--add-member',
            action='store_true',
            help='Add a test member to the team'
        )
        parser.add_argument(
            '--check-scheduling',
            action='store_true',
            help='Check if team should start auto-scheduling'
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate schedules for the team'
        )

    def handle(self, *args, **options):
        team_id = options.get('team_id')
        
        if not team_id:
            # Get the first available team
            team = Team.objects.filter(is_active=True).first()
            if not team:
                self.stdout.write(
                    self.style.ERROR('No active teams found. Please create a team first.')
                )
                return
            team_id = team.id
        
        try:
            team = Team.objects.get(id=team_id)
            self.stdout.write(f'Working with team: {team.team_name}')
            
            # Show current member count
            member_count = team.members.filter(is_active=True).count()
            self.stdout.write(f'Current member count: {member_count}')
            
            if options.get('add_member'):
                # Add a test member
                test_user, created = User.objects.get_or_create(
                    email=f'test_member_{team_id}@example.com',
                    defaults={
                        'name': f'Test Member {team_id}',
                        'role': 'member'
                    }
                )
                
                if created:
                    test_user.set_password('testpassword123')
                    test_user.save()
                    self.stdout.write(f'Created test user: {test_user.name}')
                else:
                    self.stdout.write(f'Using existing test user: {test_user.name}')
                
                # Add to team
                membership, created = TeamMembers.objects.get_or_create(
                    team=team,
                    member=test_user,
                    defaults={'is_active': True}
                )
                
                if created:
                    self.stdout.write(f'Added {test_user.name} to team {team.team_name}')
                else:
                    self.stdout.write(f'{test_user.name} is already a member of {team.team_name}')
                
                # Update member count
                member_count = team.members.filter(is_active=True).count()
                self.stdout.write(f'New member count: {member_count}')
            
            if options.get('check_scheduling'):
                # Check if team should start auto-scheduling
                self.stdout.write('Checking auto-scheduling...')
                result = check_and_start_auto_scheduling.delay(team_id)
                self.stdout.write(f'Task queued with ID: {result.id}')
                self.stdout.write('Check Celery logs for results')
            
            if options.get('regenerate'):
                # Regenerate schedules
                self.stdout.write('Regenerating schedules...')
                result = regenerate_schedules_for_team.delay(team_id)
                self.stdout.write(f'Task queued with ID: {result.id}')
                self.stdout.write('Check Celery logs for results')
            
            # Show final status
            self.stdout.write('\n=== Final Status ===')
            self.stdout.write(f'Team: {team.team_name}')
            self.stdout.write(f'Members: {team.members.filter(is_active=True).count()}')
            self.stdout.write(f'Can schedule: {team.members.filter(is_active=True).count() >= 5}')
            
            # Show schedules
            from hirethon_template.assign_task.models import Schedule
            schedules = Schedule.objects.filter(team=team)
            self.stdout.write(f'Total schedules: {schedules.count()}')
            
            for schedule in schedules:
                assigned_count = schedule.timeslots.filter(assigned_member__isnull=False).count()
                total_count = schedule.timeslots.count()
                self.stdout.write(f'  Week {schedule.week_start_date}: {assigned_count}/{total_count} timeslots assigned')
            
        except Team.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Team with ID {team_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
