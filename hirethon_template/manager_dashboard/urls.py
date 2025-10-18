from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hirethon_template.manager_dashboard.api.views import (
    ManagerDashboardViewSet,
    TeamViewSet,
    InvitationViewSet
)

router = DefaultRouter()
router.register(r'dashboard', ManagerDashboardViewSet, basename='manager-dashboard')
router.register(r'teams', TeamViewSet)
router.register(r'invitations', InvitationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
