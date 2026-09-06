from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("balance/", views.balance_general, name="balance_general"),
]
