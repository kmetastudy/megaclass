# urls.py
from django.urls import path
from . import views

app_name = 'health_habit'

urlpatterns = [
    # 학생용
    path('student/<int:slide_id>/', views.student_health_habit_view, name='student_view'),
    path('api/tracker/<int:slide_id>/', views.get_tracker_data, name='get_tracker'),
    path('api/save-promises/', views.save_promises, name='save_promises'),
    path('api/save-reflection/', views.save_reflection, name='save_reflection'),
    path('api/reflection/<int:tracker_id>/<int:promise>/<int:week>/<int:day>/', views.get_reflection, name='get_reflection'),
    path('api/reflections/<int:tracker_id>/<int:promise_num>/', views.get_promise_reflections, name='get_reflections'),
    path('api/final-reflection/<int:tracker_id>/', views.get_final_reflection, name='get_final_reflection'),
    path('api/submit/', views.submit_final, name='submit_final'),
    
    # 교사용
    path('teacher/<int:slide_id>/', views.teacher_evaluation_view, name='teacher_view'),
    path('api/teacher/students/<int:slide_id>/', views.get_students_for_evaluation, name='get_students'),
    path('api/teacher/student-detail/<int:tracker_id>/', views.get_student_detail_for_evaluation, name='student_detail'),
    path('api/teacher/evaluate-reflection/', views.evaluate_reflection, name='evaluate_reflection'),
    path('api/teacher/overall-evaluation/', views.save_overall_evaluation, name='overall_evaluation'),
]