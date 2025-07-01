from django.urls import path
from . import views

urlpatterns = [
    # 메인 페이지
    path('', views.index, name='index'),
    
    # 인증 관련
    path('api/auth/login/', views.user_login, name='login'),
    path('api/auth/logout/', views.user_logout, name='logout'),
    path('api/auth/profile/', views.user_profile, name='profile'),
    
    # 학급 및 학생 관리
    path('api/classes/', views.class_list, name='class_list'),
    path('api/classes/create/', views.class_create, name='class_create'),
    path('api/students/', views.student_list, name='student_list'),
    path('api/students/create/', views.student_create, name='student_create'),
    
    # 코스 관리
    path('api/courses/', views.course_list, name='course_list'),
    path('api/courses/create/', views.course_create, name='course_create'),
    
    # 컨텐츠 관리
    path('api/content-types/', views.content_type_list, name='content_type_list'),
    
    # 대시보드
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
]