from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Organization(models.Model):
    """
    Organization model representing different organizations in the system.
    Each organization has a manager who is responsible for it.
    """
    
    org_name = models.CharField(
        _("Organization Name"),
        max_length=255,
        help_text=_("Name of the organization")
    )
    
    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='managed_organizations',
        help_text=_("Manager responsible for this organization"),
        limit_choices_to={'role': 'manager'}  # Only users with manager role
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When the organization was created")
    )
    
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("When the organization was last updated")
    )
    
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether the organization is active")
    )

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ['org_name']
        unique_together = ['org_name', 'manager']  # Prevent duplicate org names for same manager

    def __str__(self):
        return f"{self.org_name} (Manager: {self.manager.email})"

    def get_absolute_url(self):
        """Get URL for organization's detail view."""
        return f"/organizations/{self.id}/"