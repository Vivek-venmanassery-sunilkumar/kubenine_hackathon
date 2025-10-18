from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter
from django.urls import path, include

from hirethon_template.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)

app_name = "api"
urlpatterns = [
    *router.urls,
    path("admin/", include("hirethon_template.admin_dashboard.urls")),
    path("manager/", include("hirethon_template.manager_dashboard.urls")),
]
