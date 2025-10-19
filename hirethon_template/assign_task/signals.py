from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from hirethon_template.manager_dashboard.models import TeamMembers
from .tasks import regenerate_schedules_for_team, check_and_start_auto_scheduling


@receiver(post_save, sender=TeamMembers)
def handle_team_member_added(sender, instance, created, **kwargs):
    """
    Triggered when a new team member is added or when a member's status changes.
    """
    if created and instance.is_active:
        # New member added to team
        print(f"New member {instance.member.name} added to team {instance.team.team_name}")
        
        # Only check auto-scheduling - it will handle regeneration internally
        check_and_start_auto_scheduling.delay(instance.team.id)
        
    elif not created and instance.is_active:
        # Existing member reactivated
        print(f"Member {instance.member.name} reactivated in team {instance.team.team_name}")
        
        # Regenerate schedules from tomorrow onwards
        regenerate_schedules_for_team.delay(instance.team.id)


@receiver(post_delete, sender=TeamMembers)
def handle_team_member_removed(sender, instance, **kwargs):
    """
    Triggered when a team member is removed.
    """
    print(f"Member {instance.member.name} removed from team {instance.team.team_name}")
    
    # Regenerate schedules from tomorrow onwards to reflect member removal
    regenerate_schedules_for_team.delay(instance.team.id)
