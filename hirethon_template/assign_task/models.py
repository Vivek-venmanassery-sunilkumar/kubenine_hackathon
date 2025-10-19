from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from hirethon_template.manager_dashboard.models import Team
from datetime import datetime, timedelta
import uuid

User = get_user_model()


class TeamScheduleConfig(models.Model):
    """Configuration for team scheduling rules."""
    
    team = models.OneToOneField(
        Team,
        on_delete=models.CASCADE,
        related_name='schedule_config',
        help_text=_("Team this configuration belongs to")
    )
    
    # Manager configurable settings
    timeslot_duration_hours = models.PositiveIntegerField(
        _("Timeslot Duration (hours)"),
        default=4,
        help_text=_("Duration of each timeslot in hours (max 8)")
    )
    
    min_break_hours = models.PositiveIntegerField(
        _("Minimum Break (hours)"),
        default=12,
        help_text=_("Minimum break between shifts in hours")
    )
    
    # Fixed system constraints (hardcoded)
    MAX_DAILY_HOURS = 8
    MAX_WEEKLY_HOURS = 40
    MAX_TIMESLOT_DURATION = 8
    
    @classmethod
    def get_min_team_size_for_scheduling(cls):
        """Get minimum team size required to start scheduling."""
        return 5
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When the configuration was created")
    )
    
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("When the configuration was last updated")
    )
    
    class Meta:
        verbose_name = _("Team Schedule Configuration")
        verbose_name_plural = _("Team Schedule Configurations")
    
    def __str__(self):
        return f"Schedule Config for {self.team.team_name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.timeslot_duration_hours > self.MAX_TIMESLOT_DURATION:
            raise ValidationError(f"Timeslot duration cannot exceed {self.MAX_TIMESLOT_DURATION} hours")
        if self.timeslot_duration_hours <= 0:
            raise ValidationError("Timeslot duration must be positive")
        
        if self.min_break_hours <= 0:
            raise ValidationError("Minimum break hours must be positive")
        if self.min_break_hours > 24:
            raise ValidationError("Minimum break hours cannot exceed 24 hours")


class Schedule(models.Model):
    """Weekly schedule for a team."""
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text=_("Team this schedule belongs to")
    )
    
    week_start_date = models.DateField(
        _("Week Start Date"),
        help_text=_("Monday of the week this schedule covers")
    )
    
    week_end_date = models.DateField(
        _("Week End Date"),
        help_text=_("Sunday of the week this schedule covers")
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ('published', _('Published')),
            ('archived', _('Archived')),
        ],
        default='published',
        help_text=_("Current status of the schedule")
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When the schedule was created")
    )
    
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("When the schedule was last updated")
    )
    
    class Meta:
        verbose_name = _("Schedule")
        verbose_name_plural = _("Schedules")
        unique_together = ['team', 'week_start_date']
        ordering = ['-week_start_date']
    
    def __str__(self):
        return f"Schedule for {self.team.team_name} - Week of {self.week_start_date}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate week_end_date
        if self.week_start_date and not self.week_end_date:
            self.week_end_date = self.week_start_date + timedelta(days=6)
        super().save(*args, **kwargs)


class Timeslot(models.Model):
    """Individual timeslot within a schedule."""
    
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='timeslots',
        help_text=_("Schedule this timeslot belongs to")
    )
    
    assigned_member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_timeslots',
        null=True,
        blank=True,
        help_text=_("Member assigned to this timeslot")
    )
    
    start_datetime = models.DateTimeField(
        _("Start DateTime"),
        help_text=_("When this timeslot starts")
    )
    
    end_datetime = models.DateTimeField(
        _("End DateTime"),
        help_text=_("When this timeslot ends")
    )
    
    is_break = models.BooleanField(
        _("Is Break"),
        default=False,
        help_text=_("Whether this is a break period (no assignment needed)")
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When the timeslot was created")
    )
    
    class Meta:
        verbose_name = _("Timeslot")
        verbose_name_plural = _("Timeslots")
        ordering = ['start_datetime']
    
    def __str__(self):
        if self.assigned_member:
            return f"{self.start_datetime} - {self.end_datetime} ({self.assigned_member.name})"
        return f"{self.start_datetime} - {self.end_datetime} (Unassigned)"
    
    @property
    def duration_hours(self):
        """Calculate duration in hours."""
        if self.end_datetime and self.start_datetime:
            delta = self.end_datetime - self.start_datetime
            return delta.total_seconds() / 3600
        return 0


class ScheduleValidation(models.Model):
    """Track validation results for schedules."""
    
    schedule = models.OneToOneField(
        Schedule,
        on_delete=models.CASCADE,
        related_name='validation',
        help_text=_("Schedule this validation belongs to")
    )
    
    is_valid = models.BooleanField(
        _("Is Valid"),
        default=False,
        help_text=_("Whether the schedule passes all validation rules")
    )
    
    has_sufficient_members = models.BooleanField(
        _("Has Sufficient Members"),
        default=False,
        help_text=_("Whether there are enough members to cover all timeslots")
    )
    
    validation_errors = models.JSONField(
        _("Validation Errors"),
        default=list,
        help_text=_("List of validation error messages")
    )
    
    validation_warnings = models.JSONField(
        _("Validation Warnings"),
        default=list,
        help_text=_("List of validation warning messages")
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When the validation was performed")
    )
    
    class Meta:
        verbose_name = _("Schedule Validation")
        verbose_name_plural = _("Schedule Validations")
    
    def __str__(self):
        return f"Validation for {self.schedule} - {'Valid' if self.is_valid else 'Invalid'}"


class SwapRequest(models.Model):
    """Model for managing slot swap requests between team members."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('rejected', _('Rejected')),
        ('processed', _('Processed')),
        ('expired', _('Expired')),
    ]
    
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='swap_requests_sent',
        help_text=_("Member requesting the swap")
    )
    
    responder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='swap_requests_received',
        help_text=_("Member being asked to swap")
    )
    
    requester_slot = models.ForeignKey(
        'Timeslot',
        on_delete=models.CASCADE,
        related_name='swap_requests_as_requester',
        help_text=_("Slot the requester wants to give up")
    )
    
    responder_slot = models.ForeignKey(
        'Timeslot',
        on_delete=models.CASCADE,
        related_name='swap_requests_as_responder',
        help_text=_("Slot the responder is being asked to give up")
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text=_("Current status of the swap request")
    )
    
    request_date = models.DateTimeField(
        _("Request Date"),
        auto_now_add=True,
        help_text=_("When the swap was requested")
    )
    
    deadline = models.DateTimeField(
        _("Deadline"),
        help_text=_("24 hours before the first slot starts")
    )
    
    processed_at = models.DateTimeField(
        _("Processed At"),
        null=True,
        blank=True,
        help_text=_("When the swap was processed")
    )
    
    rejection_reason = models.TextField(
        _("Rejection Reason"),
        blank=True,
        help_text=_("Reason for rejection if applicable")
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When the swap request was created")
    )
    
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("When the swap request was last updated")
    )
    
    class Meta:
        verbose_name = _("Swap Request")
        verbose_name_plural = _("Swap Requests")
        ordering = ['-created_at']
        unique_together = ['requester_slot', 'responder_slot']
    
    def __str__(self):
        return f"Swap: {self.requester.name} ↔ {self.responder.name}"
    
    def is_valid(self):
        """Check if the swap request is still valid."""
        from django.utils import timezone
        return (
            self.status == 'pending' and
            timezone.now() < self.deadline and
            self.requester_slot.assigned_member == self.requester and
            self.responder_slot.assigned_member == self.responder
        )
    
    def can_be_accepted(self):
        """Check if the swap can be accepted."""
        return self.is_valid() and self.status == 'pending'
    
    def accept(self):
        """Accept the swap request and process it immediately."""
        if not self.can_be_accepted():
            return False
        
        try:
            # Swap the assignments
            temp_member = self.requester_slot.assigned_member
            self.requester_slot.assigned_member = self.responder_slot.assigned_member
            self.responder_slot.assigned_member = temp_member
            
            # Update timestamps
            from django.utils import timezone
            self.requester_slot.updated_at = timezone.now()
            self.responder_slot.updated_at = timezone.now()
            
            # Save changes
            self.requester_slot.save()
            self.responder_slot.save()
            
            # Mark as processed
            self.status = 'processed'
            self.processed_at = timezone.now()
            self.save()
            
            return True
            
        except Exception as e:
            # Log error and mark as failed
            self.status = 'rejected'
            self.rejection_reason = f"Processing failed: {str(e)}"
            self.save()
            return False
    
    def reject(self, reason=""):
        """Reject the swap request."""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()