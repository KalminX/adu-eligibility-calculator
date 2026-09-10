"""
URL configuration for calculator app.
"""

from django.urls import path
from . import views

app_name = "calculator"

urlpatterns = [
    path("", views.index, name="index"),
    path("calculator/", views.index, name="calculator_index"),
    path("calculator/questions/", views.questions_view, name="questions"),
    path("calculator/result/", views.result_view, name="result"),
    path("calculator/restart/", views.restart_view, name="restart"),
]
