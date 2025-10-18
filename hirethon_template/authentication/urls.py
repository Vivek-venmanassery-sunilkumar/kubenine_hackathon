from django.urls import path
from .api import views

app_name = "authentication"

urlpatterns = [
    # Authentication endpoints
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("refresh/", views.refresh_token, name="refresh-token"),
    path("roles/", views.get_roles, name="get-roles"),

    # Registration endpoints
    path("register/manager/", views.register_manager, name="register-manager"),
    # path("register/member/", views.register_member, name="register-member"),
    # path("register/admin/", views.register_admin, name="register-admin"),

    # User management endpoints
    # path("users/", views.list_users, name="list-users"),
    # path("users/<int:user_id>/", views.user_detail, name="user-detail"),
]
