from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hirethon_template.admin_dashboard.api.views import (
    AdminDashboardViewSet,
    OrganizationViewSet,
    ManagerViewSet
)

router = DefaultRouter()
router.register(r'dashboard', AdminDashboardViewSet, basename='admin-dashboard')
router.register(r'organizations', OrganizationViewSet)
router.register(r'managers', ManagerViewSet, basename='managers')

urlpatterns = [
    path('', include(router.urls)),
]
