# core/urls.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "login/",
        LoginView.as_view(
            template_name="core/login.html",
            redirect_authenticated_user=True,
            next_page=reverse_lazy("dashboard"),
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("login")), name="logout"),
    path("balance/", views.balance_general, name="balance_general"),
    path("api/user/", views.UserView.as_view(), name="user"),
]
