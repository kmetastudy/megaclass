from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # 웹 페이지
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # API (기존 JavaScript와 호환성)
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/profile/', views.api_profile, name='api_profile'),

    # 교사 회원가입 페이지 뷰
    path('register/teacher/', views.teacher_register_view, name='teacher_register'),
     # ★★★ 교사 회원가입 처리를 위한 API 엔드포인트 추가 ★★★
    path('api/register/teacher/', views.api_teacher_register, name='api_teacher_register'),
]