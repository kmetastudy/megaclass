from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [

     # 대시보드
    path('', views.dashboard_view, name='dashboard'),
    
    # 코스 관련
    path('courses/', views.course_list_view, name='course_list'),
    path('course/<int:course_id>/', views.learning_course_view, name='learning_course'),
    
    #기록 관련
    path('my-records/', views.my_records_view, name='my_records'),
    
    # 학습 관련
    path('slide/<int:slide_id>/', views.slide_view, name='slide_view'),
    path('slide/<int:slide_id>/note/', views.save_note_ajax, name='save_note_ajax'),
    
    # 진도 및 성적
    path('progress/', views.progress_view, name='progress'),
    path('my-answers/', views.my_answers_view, name='my_answers'),
    
    # API endpoints
    path('api/progress/<int:course_id>/', views.course_progress_api, name='course_progress_api'),

    # 답안처리 로직

    path('check-answer/', views.check_answer, name='check_answer'),
      # ★★★★★ [추가] one-shot-submit 유형 답안 제출을 위한 URL ★★★★★
    path('submit-answer/', views.submit_answer, name='submit_answer'),
    # ★★★★★ [추가] physical_record 유형 답안 제출을 위한 URL ★★★★★
    path('submit-physical-record/', views.submit_physical_record, name='submit_physical_record'),

    # ★★★★★ [추가] ordering 유형 답안 채점을 위한 URL ★★★★★
    path('check-ordering/', views.check_ordering, name='check_ordering'),
   
]