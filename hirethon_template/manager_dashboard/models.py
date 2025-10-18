from django.db import models
from django.contrib.auth import get_user_model
from hirethon_template.authentication.models import Organization
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class Team(models.Model):
    """Team model for managing teams within organizations."""
    
    team_name = models.CharField(
        max_length=255,
        help_text="Name of the team"
    )
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='teams',
        help_text="Organization this team belongs to"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the team was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the team was last updated"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the team is active"
    )
    
    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        ordering = ['team_name']
        unique_together = ['team_name', 'organization']  # Prevent duplicate team names within same organization
    
    def __str__(self):
        return f"{self.team_name} ({self.organization.org_name})"


class Invitation(models.Model):
    """Invitation model for inviting members to join a team."""
    
    email = models.EmailField(
        _("Email Address"),
        help_text=_("Email address of the person being invited")
    )
    
    token = models.UUIDField(
        _("Invitation Token"),
        default=uuid.uuid4,
        unique=True,
        help_text=_("Unique token for the invitation")
    )
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='invitations',
        help_text=_("Team the person is being invited to join")
    )
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
        help_text=_("Organization the person is being invited to")
    )
    
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        help_text=_("Manager who sent the invitation")
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('accepted', _('Accepted')),
            ('expired', _('Expired')),
            ('cancelled', _('Cancelled')),
        ],
        default='pending',
        help_text=_("Current status of the invitation")
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When the invitation was created")
    )
    
    expires_at = models.DateTimeField(
        _("Expires At"),
        help_text=_("When the invitation expires")
    )
    
    accepted_at = models.DateTimeField(
        _("Accepted At"),
        null=True,
        blank=True,
        help_text=_("When the invitation was accepted")
    )
    
    class Meta:
        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")
        ordering = ['-created_at']
        unique_together = ['email', 'team']  # Prevent duplicate invitations for same email/team
    
    def __str__(self):
        return f"Invitation for {self.email} to {self.team.team_name} ({self.organization.org_name})"
    
    def is_expired(self):
        """Check if the invitation has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def get_invitation_url(self):
        """Get the full invitation URL."""
        from django.conf import settings
        return f"{settings.FRONTEND_URL}/register?token={self.token}&email={self.email}&team_id={self.team.id}"


class TeamMembers(models.Model):
    """TeamMembers model for managing team memberships."""
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members',
        help_text=_("Team the member belongs to")
    )
    
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='team_memberships',
        help_text=_("User who is a member of the team")
    )
    
    joined_at = models.DateTimeField(
        _("Joined At"),
        auto_now_add=True,
        help_text=_("When the member joined the team")
    )
    
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether the membership is active")
    )
    
    class Meta:
        verbose_name = _("Team Member")
        verbose_name_plural = _("Team Members")
        ordering = ['-joined_at']
        unique_together = ['team', 'member']  # Prevent duplicate memberships
    
    def __str__(self):
        return f"{self.member.name} in {self.team.team_name}"
