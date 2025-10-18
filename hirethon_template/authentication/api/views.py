from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from hirethon_template.users.enums import UserRole
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
    
    if not email or not password:
        return Response(
            {"error": "Email and password are required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "User with this email already exists."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create the manager user
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=UserRole.MANAGER
        )
        
        return Response(
            {
                "message": "Manager registered successfully.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role
                }
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to create manager: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([])  # No authentication required for login
def login(request):
    """
    Login endpoint that returns JWT tokens and user role information.
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {"error": "Email and password are required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate user
    user = authenticate(request, email=email, password=password)
    
    if not user:
        return Response(
            {"error": "Invalid email or password."}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {"error": "User account is disabled."}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate JWT tokens
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


@api_view(['POST'])
@permission_classes([])  # No authentication required for refresh
def refresh_token(request):
    """
    Refresh access token using refresh token.
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {"error": "Refresh token is required."}, 
            status=status.HTTP_400_BAD_REQUEST
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
        return Response(
            {"error": "Invalid refresh token."}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([])  # No authentication required for logout
def logout(request):
    """
    Logout endpoint that clears cookies.
    """
    response = Response(
        {"message": "Logout successful"},
        status=status.HTTP_200_OK
    )

    # Clear cookies
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Require authentication for roles check
def get_roles(request):
    """
    Get user roles and permissions.
    Returns role information for the authenticated user.
    """

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

    return Response(response_data, status=status.HTTP_200_OK)


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
    from hirethon_template.manager_dashboard.models import Invitation, TeamMembers
    
    token = request.data.get('token')
    email = request.data.get('email')
    name = request.data.get('name')
    password = request.data.get('password')
    team_id = request.data.get('team_id')
    
    if not all([token, email, name, password, team_id]):
        return Response(
            {"error": "Token, email, name, password, and team_id are required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate invitation
        invitation = Invitation.objects.get(
            token=token,
            email=email,
            team_id=team_id,
            status='pending'
        )
        
        # Check if invitation is expired
        if invitation.is_expired():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {"error": "Invitation has expired."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the member user
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=UserRole.MEMBER
        )
        
        # Add user to team
        TeamMembers.objects.create(
            team=invitation.team,
            member=user
        )
        
        # Mark invitation as accepted
        from django.utils import timezone
        invitation.status = 'accepted'
        invitation.accepted_at = timezone.now()
        invitation.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response(
            {
                "message": "Registration successful.",
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
            },
            status=status.HTTP_201_CREATED
        )
        
    except Invitation.DoesNotExist:
        return Response(
            {"error": "Invalid invitation token or invitation not found."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"Registration failed: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
