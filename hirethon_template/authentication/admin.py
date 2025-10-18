from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import Organization

User = get_user_model()


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model."""
    
    list_display = [
        'org_name', 
        'manager', 
        'is_active', 
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'created_at',
        'updated_at',
        'manager__role'
    ]
    
    search_fields = [
        'org_name',
        'manager__email',
        'manager__name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        (_('Organization Information'), {
            'fields': ('org_name', 'manager', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter organizations to show only those managed by managers."""
        qs = super().get_queryset(request)
        return qs.select_related('manager')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit manager choices to users with manager role."""
        if db_field.name == "manager":
            kwargs["queryset"] = User.objects.filter(role='manager')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)