from django.urls import path
from . import views

app_name = 'rolling'

urlpatterns = [
    # 학생용 URL (slide_id 포함)
    path('student/<int:slide_id>/', views.student_rolling_view, name='student_view'),
    path('api/save-attempt/<int:slide_id>/', views.save_attempt, name='save_attempt'),
    path('api/get-attempts/<int:slide_id>/', views.get_student_attempts, name='get_attempts'),
    
    # 교사용 URL (개선된 버전)
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/class/<int:class_id>/', views.teacher_class_evaluation_view, name='teacher_class'),
    path('teacher/feedback-analysis/', views.get_feedback_analysis, name='feedback_analysis'),
    
    # 평가 저장
    path('save-evaluation/<int:student_id>/', views.save_evaluation, name='save_evaluation'),
    
    # API 엔드포인트
    path('api/class-stats/<int:class_id>/', views.api_class_stats, name='api_class_stats'),
    path('api/student-attempts/<int:student_id>/', views.api_student_attempts, name='api_student_attempts'),
    
    # 내보내기
    path('export-evaluations/<int:class_id>/', views.export_evaluations, name='export_evaluations'),
]