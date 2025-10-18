from django.urls import path
from .api import views

app_name = "authentication"

urlpatterns = [
    # Registration endpoints
    path("register/manager/", views.register_manager, name="register-manager"),
    # path("register/member/", views.register_member, name="register-member"),
    # path("register/admin/", views.register_admin, name="register-admin"),
    
    # Login endpoints (if custom ones are needed)
    # path("login/", views.custom_login, name="custom-login"),
    # path("logout/", views.custom_logout, name="custom-logout"),
    
    # User management endpoints
    # path("users/", views.list_users, name="list-users"),
    # path("users/<int:user_id>/", views.user_detail, name="user-detail"),
]
