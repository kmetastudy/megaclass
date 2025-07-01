# cp/urls.py
from django.urls import path
from . import views

app_name = 'cp'

urlpatterns = [
    # 메인 페이지
    path('agent/', views.cp_agent_view, name='cp_agent'),
    
    # API 엔드포인트    
    path('api/categories/', views.get_categories, name='api_categories'),
    path('api/content-types/', views.get_content_types, name='api_content_types'),
    path('api/courses/', views.get_courses, name='api_courses'),
    path('api/courses/<int:course_id>/chapters/', views.get_course_chapters, name='api_course_chapters'),
    
    
    # 컨텐츠 관련
    path('api/contents/search/', views.search_contents, name='api_search_contents'),
    path('api/contents/<int:content_id>/', views.get_content, name='api_get_content'),
    path('api/contents/create/', views.create_content, name='api_create_content'),
    path('api/contents/<int:content_id>/update/', views.update_content, name='api_update_content'),


    # 템플릿 관련 (Contents_Template 모델 사용)
    path('api/templates/search/', views.search_templates, name='api_search_templates'),
    path('api/templates/create/', views.create_template, name='api_create_template'),
    path('api/templates/<int:template_id>/', views.get_template, name='api_get_template'),
    path('api/templates/<int:template_id>/update/', views.update_template, name='api_update_template'),
    path('api/templates/<int:template_id>/delete/', views.delete_template, name='api_delete_template'),
    
    # AI 생성
    path('api/generate-content/', views.generate_content, name='api_generate_content'),
    
    # 파일 업로드 관련
    path('api/upload-image/', views.upload_image, name='api_upload_image'),
    path('api/cleanup-temp-upload/<int:attachment_id>/', views.cleanup_temp_upload, name='api_cleanup_temp_upload'),
]