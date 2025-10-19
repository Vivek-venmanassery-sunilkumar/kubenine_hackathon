from django.apps import AppConfig


class AssignTaskConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hirethon_template.assign_task"
    verbose_name = "Assign Task & Scheduling"
    
    def ready(self):
        """Import signals when the app is ready."""
        import hirethon_template.assign_task.signals