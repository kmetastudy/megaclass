from django.urls import path
from . import views

app_name = 'physical_education'

urlpatterns = [
    path('teachers/', views.teacher_dashboard, name='teacher_dashboard'),
]