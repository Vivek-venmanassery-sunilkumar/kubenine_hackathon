from django.db import models


class UserRole(models.TextChoices):
    """User role choices for the oncall scheduler application."""
    
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    MEMBER = "member", "Member"
