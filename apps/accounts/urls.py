from django.urls import path

from .views import (
    DashboardView,
    LogoutView,
    UrbanShineLoginView,
    UserCreateView,
    UserDeactivateView,
    UserDeleteView,
    UserListView,
    UserPasswordResetView,
    UserUpdateView,
)

app_name = "accounts"

urlpatterns = [
    path("login/", UrbanShineLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/new/", UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/deactivate/", UserDeactivateView.as_view(), name="user_deactivate"),
    path("users/<int:pk>/passwort/", UserPasswordResetView.as_view(), name="user_password_reset"),
    path("users/<int:pk>/loeschen/", UserDeleteView.as_view(), name="user_delete"),
]
