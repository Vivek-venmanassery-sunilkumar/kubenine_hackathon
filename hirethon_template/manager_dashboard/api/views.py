from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from hirethon_template.manager_dashboard.models import Team, Invitation
from hirethon_template.authentication.models import Organization
from hirethon_template.authentication.permissions import IsManagerOrAdmin
from hirethon_template.manager_dashboard.api.serializers import (
    TeamSerializer,
    TeamListSerializer,
    ManagerDashboardSerializer,
    ManagerStatsSerializer,
    InvitationSerializer,
    InvitationCreateSerializer,
    InvitationListSerializer
)

User = get_user_model()


class ManagerDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for manager dashboard functionality.
    """
    permission_classes = [IsManagerOrAdmin]
    
    def list(self, request):
        """
        Get manager dashboard overview data.
        """
        # TODO: Implement manager dashboard data retrieval
        return Response({
            "message": "Manager dashboard API endpoint",
            "status": "success"
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get manager dashboard statistics.
        """
        # TODO: Implement manager dashboard statistics
        return Response({
            "message": "Manager dashboard statistics",
            "status": "success"
        }, status=status.HTTP_200_OK)


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teams.
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsManagerOrAdmin]
    
    def get_queryset(self):
        """
        Filter teams based on user role.
        - Managers: Only see teams from their organization
        - Admins: Can see all teams
        """
        user = self.request.user
        
        if user.role == 'manager':
            try:
                # Get the manager's organization
                manager_org = Organization.objects.get(manager=user)
                return Team.objects.filter(organization=manager_org)
            except Organization.DoesNotExist:
                # Manager not assigned to any organization
                return Team.objects.none()
        elif user.role == 'admin':
            # Admins can see all teams
            return Team.objects.all()
        else:
            # Other roles cannot access teams
            return Team.objects.none()
    
    def perform_create(self, serializer):
        """
        Set the organization based on the manager's organization.
        Only managers can create teams, and they can only create teams for their own organization.
        """
        user = self.request.user
        
        if user.role == 'manager':
            try:
                # Get the manager's organization
                manager_org = Organization.objects.get(manager=user)
                serializer.save(organization=manager_org)
            except Organization.DoesNotExist:
                raise serializers.ValidationError("Manager is not assigned to any organization.")
        elif user.role == 'admin':
            # Admins can create teams for any organization
            # Organization should be provided in the request data
            if 'organization' not in serializer.validated_data:
                raise serializers.ValidationError("Organization is required for admin users.")
            serializer.save()
        else:
            raise serializers.ValidationError("Only managers and admins can create teams.")


class InvitationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invitations.
    """
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsManagerOrAdmin]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return InvitationCreateSerializer
        elif self.action == 'list':
            return InvitationListSerializer
        return InvitationSerializer
    
    def get_queryset(self):
        """
        Filter invitations based on user role.
        - Managers: Only see invitations from their organization
        - Admins: Can see all invitations
        """
        user = self.request.user
        
        if user.role == 'manager':
            try:
                # Get the manager's organization
                manager_org = Organization.objects.get(manager=user)
                return Invitation.objects.filter(organization=manager_org)
            except Organization.DoesNotExist:
                # Manager not assigned to any organization
                return Invitation.objects.none()
        elif user.role == 'admin':
            # Admins can see all invitations
            return Invitation.objects.all()
        else:
            # Other roles cannot access invitations
            return Invitation.objects.none()
    
    def perform_create(self, serializer):
        """
        Create invitation and send email.
        """
        invitation = serializer.save()
        
        # Send invitation email
        try:
            self._send_invitation_email(invitation)
        except Exception as e:
            # Log error but don't fail the invitation creation
            print(f"Failed to send invitation email: {e}")
    
    def _send_invitation_email(self, invitation):
        """
        Send invitation email to the invited user.
        """
        subject = f"Invitation to join {invitation.organization.org_name}"
        
        message = f"""
        Hello,
        
        You have been invited to join {invitation.organization.org_name} on the OnCall Scheduler platform.
        
        To accept this invitation, please click the link below:
        {invitation.get_invitation_url()}
        
        This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}.
        
        If you did not expect this invitation, please ignore this email.
        
        Best regards,
        {invitation.invited_by.name}
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """
        Resend invitation email.
        """
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Can only resend pending invitations.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            self._send_invitation_email(invitation)
            return Response({'message': 'Invitation email sent successfully.'})
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a pending invitation.
        """
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Can only cancel pending invitations.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.status = 'cancelled'
        invitation.save()
        
        return Response({'message': 'Invitation cancelled successfully.'})
