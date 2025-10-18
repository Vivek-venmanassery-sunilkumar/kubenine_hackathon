from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from hirethon_template.authentication.models import Organization
from hirethon_template.authentication.permissions import IsAdminUser
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


class ManagerViewSet(viewsets.ViewSet):
    """
    ViewSet for managing managers.
    """
    permission_classes = [IsAdminUser]
    
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
