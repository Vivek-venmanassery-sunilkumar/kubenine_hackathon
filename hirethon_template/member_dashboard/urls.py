from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hirethon_template.member_dashboard.api.views import (
    MemberScheduleViewSet, SwapRequestViewSet, TeamMemberViewSet
)

app_name = 'member_dashboard'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'schedule', MemberScheduleViewSet, basename='member-schedule')
router.register(r'swap-requests', SwapRequestViewSet, basename='swap-requests')
router.register(r'team-members', TeamMemberViewSet, basename='team-members')

urlpatterns = [
    path('', include(router.urls)),
]
