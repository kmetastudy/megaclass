from django.urls import path
from . import views

app_name = 'ncs'

urlpatterns = [
    # 학생용
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('session/create/', views.create_learning_session, name='create_session'),
    path('session/<int:session_id>/', views.learning_session, name='learning_session'),
    path('session/<int:session_id>/question/<int:question_id>/submit/', views.submit_answer, name='submit_answer'),
    path('session/<int:session_id>/result/', views.session_result, name='session_result'),
    path('session/<int:session_id>/save-progress/', views.save_progress, name='save_progress'),    
    path('session/<int:session_id>/complete/', views.complete_session, name='complete_session'),
    
    # 교사용
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('assignment/create/', views.create_assignment, name='create_assignment'),
    path('statistics/', views.statistics_view, name='statistics'),
    
    # API
    path('api/contents/by-subcompetency/', views.api_contents_by_subcompetency, name='api_contents_by_subcompetency'),
    path('api/competency/search/', views.api_competency_search, name='api_competency_search'),
    path('api/student/<int:student_id>/progress/', views.api_student_progress, name='api_student_progress'),
]