from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
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
