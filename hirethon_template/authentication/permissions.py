from rest_framework import permissions
from hirethon_template.users.enums import UserRole


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has admin role
        return request.user.role == UserRole.ADMIN


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow both manager and admin users.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has manager or admin role
        return request.user.role in [UserRole.MANAGER, UserRole.ADMIN]


class IsMemberOrAbove(permissions.BasePermission):
    """
    Custom permission to allow member, manager, and admin users.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has any valid role
        return request.user.role in [UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN]
