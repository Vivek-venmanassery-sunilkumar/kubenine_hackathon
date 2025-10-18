from rest_framework import serializers
from django.contrib.auth import get_user_model
from hirethon_template.authentication.models import Organization
from hirethon_template.users.enums import UserRole

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    
    manager_id = serializers.IntegerField(write_only=True, required=False)
    manager_name = serializers.CharField(source='manager.name', read_only=True)
    manager_email = serializers.CharField(source='manager.email', read_only=True)
    
    class Meta:
        model = Organization
        fields = ['id', 'org_name', 'manager_id', 'manager_name', 'manager_email', 'created_at', 'updated_at', 'is_active']
    
    def validate_manager_id(self, value):
        """Check if manager exists and has manager role."""
        try:
            User.objects.get(id=value, role=UserRole.MANAGER)
        except User.DoesNotExist:
            raise serializers.ValidationError("Manager does not exist or is not a manager.")
        return value
    
    def create(self, validated_data):
        """Create organization and assign manager."""
        manager_id = validated_data.pop('manager_id', None)
        
        if manager_id:
            manager = User.objects.get(id=manager_id)
            validated_data['manager'] = manager
        
        organization = Organization.objects.create(**validated_data)
        return organization


class ManagerRegistrationSerializer(serializers.Serializer):
    """Serializer for manager registration."""
    
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    
    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        """Create a new manager user."""
        password = validated_data.pop('password')
        
        # Create user with manager role
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            role=UserRole.MANAGER,
            password=password
        )
        
        return user


class ManagerListSerializer(serializers.ModelSerializer):
    """Serializer for listing managers."""
    
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'created_at']


class AdminDashboardSerializer(serializers.Serializer):
    """
    Serializer for admin dashboard data.
    """
    message = serializers.CharField()
    status = serializers.CharField()


class AdminStatsSerializer(serializers.Serializer):
    """
    Serializer for admin dashboard statistics.
    """
    total_users = serializers.IntegerField(required=False)
    total_orders = serializers.IntegerField(required=False)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    active_sessions = serializers.IntegerField(required=False)
