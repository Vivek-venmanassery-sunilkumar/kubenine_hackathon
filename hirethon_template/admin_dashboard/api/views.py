from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from hirethon_template.authentication.models import Organization
from hirethon_template.authentication.permissions import IsAdminUser
from hirethon_template.users.enums import UserRole
from hirethon_template.utils.error_handling import (
    handle_database_error, create_success_response,
    create_validation_error_response, create_conflict_error_response,
    create_not_found_error_response, create_internal_error_response
)
from hirethon_template.admin_dashboard.api.serializers import (
    OrganizationSerializer,
    ManagerRegistrationSerializer,
    ManagerListSerializer,
    AdminDashboardSerializer,
    AdminStatsSerializer
)

User = get_user_model()


class AdminDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for admin dashboard functionality.
    """
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        """
        Get admin dashboard overview data.
        """
        # TODO: Implement admin dashboard data retrieval
        return Response({
            "message": "Admin dashboard API endpoint",
            "status": "success"
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get admin dashboard statistics.
        """
        # TODO: Implement admin dashboard statistics
        return Response({
            "message": "Admin dashboard statistics",
            "status": "success"
        }, status=status.HTTP_200_OK)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing organizations.
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        """
        Update an organization with proper error handling.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
            
            if serializer.is_valid():
                # Check for unique constraint violations before saving
                org_name = serializer.validated_data.get('org_name', instance.org_name)
                manager_id = serializer.validated_data.get('manager_id')
                
                if manager_id:
                    try:
                        manager = User.objects.get(id=manager_id, role=UserRole.MANAGER)
                        
                        # Check if the new manager is already assigned to another organization
                        if Organization.objects.filter(manager=manager, is_active=True).exclude(id=instance.id).exists():
                            return create_conflict_error_response(
                                "This manager is already assigned to another organization.",
                                {"field": "manager_id", "value": manager_id, "manager_email": manager.email}
                            )
                    except User.DoesNotExist:
                        return create_not_found_error_response(
                            "Manager not found or is not a manager.",
                            {"manager_id": manager_id}
                        )
                else:
                    manager = instance.manager
                
                # Check if the combination of org_name and manager already exists (excluding current instance)
                if Organization.objects.filter(
                    org_name=org_name, 
                    manager=manager
                ).exclude(id=instance.id).exists():
                    return create_conflict_error_response(
                        "An organization with this name already exists for the selected manager.",
                        {"field": "org_name", "value": org_name, "manager": manager.email}
                    )
                
                # Save the organization
                organization = serializer.save()
                
                # Return updated organization data
                response_serializer = OrganizationSerializer(organization)
                return create_success_response(
                    "Organization updated successfully.",
                    response_serializer.data
                )
            else:
                # Handle validation errors
                field_errors = {}
                for field, errors in serializer.errors.items():
                    field_errors[field] = errors[0] if errors else "Invalid value"
                
                return create_validation_error_response(
                    "Please correct the errors below.",
                    field_errors
                )
                
        except (IntegrityError, DjangoValidationError) as e:
            # Handle database and validation errors
            api_error = handle_database_error(e, "organization update")
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
                "Failed to update organization. Please try again later.",
                {"original_error": str(e)}
            )


class ManagerViewSet(viewsets.ViewSet):
    """
    ViewSet for managing managers.
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get managers who are not assigned to any organization.
        """
        try:
            # Get managers who are not assigned to any active organization
            assigned_manager_ids = Organization.objects.filter(is_active=True).values_list('manager_id', flat=True)
            available_managers = User.objects.filter(
                role=UserRole.MANAGER,
                is_active=True
            ).exclude(id__in=assigned_manager_ids)
            
            serializer = ManagerListSerializer(available_managers, many=True)
            return create_success_response(
                "Available managers retrieved successfully.",
                {"managers": serializer.data}
            )
        except Exception as e:
            return create_internal_error_response(
                "Failed to retrieve available managers. Please try again later.",
                {"original_error": str(e)}
            )
    
    def list(self, request):
        """
        List all managers.
        """
        managers = User.objects.filter(role='manager')
        serializer = ManagerListSerializer(managers, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Register a new manager.
        """
        serializer = ManagerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Return the created manager data
            manager_data = ManagerListSerializer(user).data
            return Response(manager_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific manager.
        """
        try:
            manager = User.objects.filter(role='manager', id=pk).first()
            if not manager:
                return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ManagerListSerializer(manager)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        Update a manager.
        """
        try:
            # Get the manager to update
            try:
                manager = User.objects.get(id=pk, role=UserRole.MANAGER)
            except User.DoesNotExist:
                return create_not_found_error_response(
                    "Manager not found.",
                    {"manager_id": pk}
                )
            
            # Get update data
            name = request.data.get('name')
            email = request.data.get('email')
            password = request.data.get('password')
            
            # Validate required fields
            if not name or not email:
                return create_validation_error_response(
                    "Name and email are required.",
                    {"name": "This field is required" if not name else None,
                     "email": "This field is required" if not email else None}
                )
            
            # Check if email is being changed and if it conflicts with existing users
            if email != manager.email:
                if User.objects.filter(email=email).exclude(id=pk).exists():
                    return create_conflict_error_response(
                        "A user with this email already exists.",
                        {"field": "email", "value": email}
                    )
            
            # Update manager fields
            manager.name = name
            manager.email = email
            
            # Update password if provided
            if password:
                if len(password) < 8:
                    return create_validation_error_response(
                        "Password must be at least 8 characters long.",
                        {"password": "Password must be at least 8 characters long"}
                    )
                manager.set_password(password)
            
            manager.save()
            
            # Return updated manager data
            serializer = ManagerListSerializer(manager)
            return create_success_response(
                "Manager updated successfully.",
                serializer.data
            )
            
        except (IntegrityError, DjangoValidationError) as e:
            # Handle database and validation errors
            api_error = handle_database_error(e, "manager update")
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
                "Failed to update manager. Please try again later.",
                {"original_error": str(e)}
            )
    
    def destroy(self, request, pk=None):
        """
        Delete a manager.
        """
        try:
            manager = User.objects.filter(role='manager', id=pk).first()
            if not manager:
                return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)
            
            manager.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
