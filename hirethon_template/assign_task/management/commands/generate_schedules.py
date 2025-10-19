from django.core.management.base import BaseCommand
from hirethon_template.assign_task.tasks import generate_weekly_schedules, validate_all_draft_schedules, auto_publish_valid_schedules


class Command(BaseCommand):
    help = 'Manually trigger schedule generation tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['generate', 'validate', 'publish', 'all'],
            default='all',
            help='Which task to run'
        )

    def handle(self, *args, **options):
        task = options['task']
        
        if task == 'generate' or task == 'all':
            self.stdout.write('Generating weekly schedules...')
            result = generate_weekly_schedules.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Generate schedules task queued: {result.id}')
            )
        
        if task == 'validate' or task == 'all':
            self.stdout.write('Validating draft schedules...')
            result = validate_all_draft_schedules.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Validate schedules task queued: {result.id}')
            )
        
        if task == 'publish' or task == 'all':
            self.stdout.write('Auto-publishing valid schedules...')
            result = auto_publish_valid_schedules.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Auto-publish schedules task queued: {result.id}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('All requested tasks have been queued!')
        )
