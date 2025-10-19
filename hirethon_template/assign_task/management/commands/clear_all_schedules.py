from django.core.management.base import BaseCommand
from hirethon_template.assign_task.models import Schedule, Timeslot, ScheduleValidation, MemberWeeklyHours
from hirethon_template.manager_dashboard.models import Team


class Command(BaseCommand):
    help = 'Clear all schedule data to start fresh'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all schedule data'
        )

    def handle(self, *args, **options):
        if not options.get('confirm'):
            self.stdout.write(
                self.style.WARNING('This will delete ALL schedule data!')
            )
            self.stdout.write('Use --confirm flag to proceed')
            return

        self.stdout.write('=== CLEARING ALL SCHEDULE DATA ===')

        # Show current data
        self.stdout.write(f'Before cleanup:')
        self.stdout.write(f'  Schedules: {Schedule.objects.count()}')
        self.stdout.write(f'  Timeslots: {Timeslot.objects.count()}')
        self.stdout.write(f'  Schedule Validations: {ScheduleValidation.objects.count()}')
        self.stdout.write(f'  Member Weekly Hours: {MemberWeeklyHours.objects.count()}')

        # Clear all schedule-related data
        self.stdout.write('\nClearing data...')
        
        Timeslot.objects.all().delete()
        self.stdout.write('  ✓ Deleted all timeslots')

        ScheduleValidation.objects.all().delete()
        self.stdout.write('  ✓ Deleted all schedule validations')

        MemberWeeklyHours.objects.all().delete()
        self.stdout.write('  ✓ Deleted all member weekly hours')

        Schedule.objects.all().delete()
        self.stdout.write('  ✓ Deleted all schedules')

        # Show final state
        self.stdout.write(f'\nAfter cleanup:')
        self.stdout.write(f'  Schedules: {Schedule.objects.count()}')
        self.stdout.write(f'  Timeslots: {Timeslot.objects.count()}')
        self.stdout.write(f'  Schedule Validations: {ScheduleValidation.objects.count()}')
        self.stdout.write(f'  Member Weekly Hours: {MemberWeeklyHours.objects.count()}')

        self.stdout.write(
            self.style.SUCCESS('\n✅ All schedule data cleared successfully!')
        )
        self.stdout.write('You can now generate fresh schedules without duplicates.')
