from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from hirethon_template.users.enums import UserRole
from hirethon_template.utils.error_handling import (
    handle_database_error, create_success_response, create_created_response,
    create_validation_error_response, create_conflict_error_response,
    create_unauthorized_error_response, create_internal_error_response,
    APIError
)
from ..permissions import IsAdminUser

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAdminUser])
def register_manager(request):
    """
    Register a new manager user.
    Only admins can register managers.
    """
    email = request.data.get('email')
    password = request.data.get('password')
    name = request.data.get('name', '')
    
    # Validate required fields
    if not email or not password:
        return create_validation_error_response(
            "Email and password are required.",
            {"email": "This field is required" if not email else None,
             "password": "This field is required" if not password else None}
        )
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return create_conflict_error_response(
            "A manager with this email already exists.",
            {"field": "email", "value": email}
        )
    
    # Create the manager user
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=UserRole.MANAGER
        )
        
        return create_created_response(
            "Manager registered successfully.",
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role
                }
            }
        )
    except (IntegrityError, DjangoValidationError) as e:
        # Handle database and validation errors
        api_error = handle_database_error(e, "manager registration")
        return Response(
            {
                "error": api_error.message,
                "error_code": api_error.error_code,
                "details": api_error.details
            },
            status=api_error.status_code
        )
    except Exception as e:
        # Handle any other unexpected errors
        return create_internal_error_response(
            "Failed to create manager. Please try again later.",
            {"original_error": str(e)}
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # No authentication required for login
def login(request):
    """
    Login endpoint that returns JWT tokens and user role information.
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    # Validate required fields
    if not email or not password:
        return create_validation_error_response(
            "Email and password are required.",
            {"email": "This field is required" if not email else None,
             "password": "This field is required" if not password else None}
        )
    
    # Authenticate user
    user = authenticate(request, email=email, password=password)
    
    if not user:
        return create_unauthorized_error_response(
            "Invalid email or password.",
            {"field": "credentials", "attempted_email": email}
        )
    
    if not user.is_active:
        return create_unauthorized_error_response(
            "Your account has been disabled. Please contact support.",
            {"field": "account_status", "status": "disabled"}
        )
    
    # Check if manager is associated with an organization
    if user.role == UserRole.MANAGER:
        from hirethon_template.authentication.models import Organization
        if not Organization.objects.filter(manager=user, is_active=True).exists():
            return create_unauthorized_error_response(
                "You are not associated with any organization. Please contact an administrator.",
                {"field": "organization", "status": "not_assigned"}
            )
    
    # Generate JWT tokens
    try:
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Prepare response data (no tokens in response body)
        response_data = {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            }
        }
        
        # Create response
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set HTTP-only cookies
        response.set_cookie(
            'access_token',
            str(access_token),
            max_age=30 * 60,  # 30 minutes
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax'
        )
        
        response.set_cookie(
            'refresh_token',
            str(refresh),
            max_age=7 * 24 * 60 * 60,  # 1 week
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        return create_internal_error_response(
            "Failed to generate authentication tokens. Please try again.",
            {"original_error": str(e)}
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # No authentication required for refresh
def refresh_token(request):
    """
    Refresh access token using refresh token.
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return create_validation_error_response(
            "Refresh token is required.",
            {"refresh": "This field is required"}
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token
        
        response_data = {
            "message": "Token refreshed successfully",
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Update access token cookie
        response.set_cookie(
            'access_token',
            str(access_token),
            max_age=30 * 60,  # 30 minutes
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        return create_unauthorized_error_response(
            "Invalid or expired refresh token. Please log in again.",
            {"field": "refresh_token", "error_type": "invalid_token"}
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # No authentication required for logout
def logout(request):
    """
    Logout endpoint that clears cookies.
    """
    try:
        response = create_success_response("Logout successful")

        # Clear cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response
        
    except Exception as e:
        return create_internal_error_response(
            "Failed to logout properly. Please try again.",
            {"original_error": str(e)}
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Require authentication for roles check
def get_roles(request):
    """
    Get user roles and permissions.
    Returns role information for the authenticated user.
    """
    try:
        user = request.user
        
        # Determine role flags
        is_admin = user.role == UserRole.ADMIN
        is_manager = user.role == UserRole.MANAGER
        is_member = user.role == UserRole.MEMBER

        response_data = {
            "is_admin": is_admin,
            "is_manager": is_manager,
            "is_member": is_member,
            "name": user.name,
            "role": user.role,
            "email": user.email,
            "id": user.id
        }

        return create_success_response("User roles retrieved successfully", response_data)
        
    except Exception as e:
        return create_internal_error_response(
            "Failed to retrieve user roles. Please try again.",
            {"original_error": str(e)}
        )


# Example of using other permission classes:
# 
# @api_view(['GET'])
# @permission_classes([IsManagerOrAdmin])
# def manager_dashboard(request):
#     """Only managers and admins can access this view."""
#     pass
#
# @api_view(['GET'])
# @permission_classes([IsMemberOrAbove])
# def user_profile(request):
#     """All authenticated users can access this view."""
#     pass


@api_view(['POST'])
@permission_classes([AllowAny])
def register_with_invitation(request):
    """
    Register a new member user using an invitation token.
    """
    from hirethon_template.manager_dashboard.models import Invitation, TeamMembers, MemberTimezones
    
    token = request.data.get('token')
    email = request.data.get('email')
    name = request.data.get('name')
    password = request.data.get('password')
    team_id = request.data.get('team_id')
    timezone = request.data.get('timezone')
    
    # Validate required fields
    required_fields = {
        'token': token,
        'email': email,
        'name': name,
        'password': password,
        'team_id': team_id,
        'timezone': timezone
    }
    
    missing_fields = {field: "This field is required" for field, value in required_fields.items() if not value}
    
    if missing_fields:
        return create_validation_error_response(
            "All fields are required for registration.",
            missing_fields
        )
    
    try:
        # Validate invitation
        try:
            invitation = Invitation.objects.get(
                token=token,
                email=email,
                team_id=team_id,
                status='pending'
            )
        except Invitation.DoesNotExist:
            return create_validation_error_response(
                "Invalid invitation token or invitation not found.",
                {"token": "Invalid or expired invitation token"}
            )
        
        # Check if invitation is expired
        if invitation.is_expired():
            invitation.status = 'expired'
            invitation.save()
            return create_validation_error_response(
                "This invitation has expired.",
                {"token": "Invitation has expired", "expired_at": str(invitation.expires_at)}
            )
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return create_conflict_error_response(
                "A user with this email already exists.",
                {"field": "email", "value": email}
            )
        
        # Create the member user
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=UserRole.MEMBER
        )
        
        # Add user to team
        team_membership = TeamMembers.objects.create(
            team=invitation.team,
            member=user
        )
        
        # Save user's timezone preference
        MemberTimezones.objects.create(
            user=user,
            timezone=timezone
        )
        
        # Mark invitation as accepted
        from django.utils import timezone as django_timezone
        invitation.status = 'accepted'
        invitation.accepted_at = django_timezone.now()
        invitation.save()
        
        # Trigger schedule regeneration for the team
        # This will be handled by the Django signal automatically
        print(f"Member {user.name} successfully added to team {invitation.team.team_name}")
        print("Schedule regeneration will be triggered automatically via signals")
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return create_created_response(
            "Registration successful.",
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role
                },
                "tokens": {
                    "access": str(access_token),
                    "refresh": str(refresh)
                }
            }
        )
        
    except (IntegrityError, DjangoValidationError) as e:
        # Handle database and validation errors
        api_error = handle_database_error(e, "member registration")
        return Response(
            {
                "error": api_error.message,
                "error_code": api_error.error_code,
                "details": api_error.details
            },
            status=api_error.status_code
        )
    except Exception as e:
        return create_internal_error_response(
            "Registration failed. Please try again later.",
            {"original_error": str(e)}
        )


