from django.urls import path
from . import views, courses,contents_views,chasi_views,statistics_views

app_name = 'teacher'

urlpatterns = [
    # ========================================
    # 대시보드
    # ========================================
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('app_home/', views.app_home, name='app_home'),
    path('api/get-slides/', views.get_slides_api, name='get_slides_api'),
    # teacher/urls.py에 추가
    path('api/content-types/', views.api_content_types, name='api_content_types'),
    path('api/chapters/<int:chapter_id>/subchapters/', views.api_chapter_subchapters, name='api_chapter_subchapters'),
    # ========================================
    # 학급 관리
    # ========================================
    path('classes/', views.class_list_view, name='class_list'),
    path('classes/create/', views.class_create_view, name='class_create'),
    path('classes/<int:class_id>/', views.class_detail_view, name='class_detail'),
    
    # ========================================
    # 학생 관리
    # ========================================
    path('students/', views.student_list_view, name='student_list'),
    path('students/create/', views.student_create_view, name='student_create'),
    path('students/<int:student_id>/', views.student_detail_view, name='student_detail'),
    # ★★★ 이미지 URL을 CSV 업로드 URL로 변경 ★★★
    path('students/bulk_create_csv/', views.bulk_student_create_from_csv_view, name='bulk_student_create_from_csv'),
    # ★★★ 샘플 CSV 다운로드 URL 추가 ★★★
    path('students/sample_csv/', views.download_sample_csv_view, name='download_sample_csv'),

    path('students/<int:student_id>/edit/', views.student_edit_view, name='student_edit'),
    path('students/<int:student_id>/delete/', views.student_delete_view, name='student_delete'),
    path('students/<int:student_id>/reset-password/', views.student_reset_password_view, name='student_reset_password'),
    
    # ========================================
    # 통계 (기존 + 신규 추가)
    # ========================================
    path('statistics/', views.statistics_view, name='statistics'),
    path('statistics/dashboard/', statistics_views.statistics_dashboard_view, name='statistics_dashboard'),
    path('statistics/by-class/', statistics_views.statistics_by_class_view, name='statistics_by_class'),
    path('statistics/by-course/', statistics_views.statistics_by_course_view, name='statistics_by_course'),
    path('statistics/submissions/', statistics_views.submission_analysis_view, name='submission_analysis'),
    path('statistics/weakness/', statistics_views.weakness_analysis_view, name='weakness_analysis'),
    path('statistics/physical-records/', statistics_views.physical_records_view, name='physical_records'),
    path('statistics/export/', statistics_views.export_statistics_view, name='export_statistics'),
    
    # 통계 API
    path('api/statistics/summary/', statistics_views.api_statistics_summary, name='api_statistics_summary'),
    path('statistics/', views.statistics_view, name='statistics'),
    # teacher/urls.py에 추가
    path('api/student-detail/', statistics_views.api_student_detail, name='api_student_detail'),
    path('api/class-performance/', statistics_views.api_class_performance_chart, name='api_class_performance_chart'),
        
    # ========================================
    # 코스 관리 (courses.py)
    # ========================================
    path('course_dashboard/',views.course_dashboard_view,name='course_dashboard'),
    path('courses/', courses.course_list_view, name='course_list'),
    path('courses/create/', courses.course_create_view, name='course_create'),
    path('courses/<int:course_id>/', courses.course_detail_view, name='course_detail'),
    path('courses/<int:course_id>/edit/', courses.course_edit_view, name='course_edit'),
    path('courses/<int:course_id>/delete/', courses.course_delete_view, name='course_delete'),
    path('courses/<int:course_id>/assign/', courses.course_assign_view, name='course_assign'),
    path('courses/<int:course_id>/structure/', courses.course_structure_manage_view, name='course_structure_manage'),
    
    # ========================================
    # 대단원 관리 (courses.py)
    # ========================================
    path('courses/<int:course_id>/chapters/', courses.chapter_list_view, name='chapter_list'),
    path('courses/<int:course_id>/chapters/create/', courses.chapter_create_view, name='chapter_create'),
    path('courses/<int:course_id>/chapters/bulk-create/', courses.bulk_chapter_create_view, name='bulk_chapter_create'),
    path('chapters/<int:chapter_id>/edit/', courses.chapter_edit_view, name='chapter_edit'),
    path('chapters/<int:chapter_id>/delete/', courses.chapter_delete_view, name='chapter_delete'),
    
    # ========================================
    # 소단원 관리 (courses.py)
    # ========================================
    path('chapters/<int:chapter_id>/subchapters/', courses.subchapter_list_view, name='subchapter_list'),
    path('chapters/<int:chapter_id>/subchapters/create/', courses.subchapter_create_view, name='subchapter_create'),
    path('subchapters/<int:subchapter_id>/edit/', courses.subchapter_edit_view, name='subchapter_edit'),
    path('subchapters/<int:subchapter_id>/delete/', courses.subchapter_delete_view, name='subchapter_delete'),
    
    # ========================================
    # 차시 관리 (courses.py)
    # ========================================
    path('subchapters/<int:subchapter_id>/chasis/', courses.chasi_list_view, name='chasi_list'),
    path('subchapters/<int:subchapter_id>/chasis/create/', courses.chasi_create_view, name='chasi_create'),
    path('chasis/<int:chasi_id>/edit/', courses.chasi_edit_view, name='chasi_edit'),
    path('chasis/<int:chasi_id>/delete/', courses.chasi_delete_view, name='chasi_delete'),
    path('chasis/<int:chasi_id>/preview/', courses.chasi_preview_view, name='chasi_preview'),
    
    # ========================================
    # 슬라이드 관리 (courses.py)
    # ========================================
     path('chasis/<int:chasi_id>/slides/', chasi_views.chasi_slide_manage, name='chasi_slide_manage'),
    path('chasis/<int:chasi_id>/slides/add/', chasi_views.chasi_slide_add, name='chasi_slide_add'),
    path('slides/<int:slide_id>/edit/', chasi_views.chasi_slide_edit, name='chasi_slide_edit'),
    path('slides/<int:slide_id>/delete/', chasi_views.chasi_slide_delete, name='chasi_slide_delete'),
    path('api/chasis/<int:chasi_id>/slides/reorder/', chasi_views.reorder_slides, name='reorder_slides'),
    path('chasis/<int:chasi_id>/preview/', chasi_views.chasi_preview, name='chasi_preview'),
    path('slides/<int:slide_id>/content/', courses.slide_content_view, name='slide_content'),
    
    # ========================================
    # 컨텐츠 라이브러리 (courses.py)
    # ========================================
     # 콘텐츠 관리
    path('contents/', contents_views.contents_list, name='contents_list'),
    path('contents/create/', contents_views.contents_create, name='contents_create'),
    path('contents/<int:content_id>/edit/', contents_views.contents_edit, name='contents_edit'),
    path('contents/<int:content_id>/delete/', contents_views.contents_delete, name='contents_delete'),
    path('api/contents/<int:content_id>/preview/', contents_views.contents_preview, name='contents_preview'),
    path('contents/<int:content_id>/duplicate/', contents_views.contents_duplicate, name='contents_duplicate'),
    # path('contents/<int:content_id>/toggle-active/', views.contents_toggle_active, name='contents_toggle_active'),

    # 학생 관리 API (views.py)
    # ========================================
    path('api/students/search/', views.api_student_search, name='api_student_search'),
    path('api/classes/<int:class_id>/students/', views.api_class_students, name='api_class_students'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    
    # ========================================
    # 코스 관련 API (courses.py)
    # ========================================
    path('api/courses/<int:course_id>/structure/', courses.api_course_structure, name='api_course_structure'),
    path('api/courses/<int:course_id>/toggle-status/', courses.api_toggle_course_status, name='api_toggle_course_status'),
    path('api/courses/<int:course_id>/quick-stats/', courses.api_course_quick_stats, name='api_course_quick_stats'),
    # 기존 코스 관련 API 섹션에 다음 줄들을 추가
path('api/courses/<int:course_id>/chapters/', courses.api_course_chapters, name='api_course_chapters'),
path('api/chapters/<int:chapter_id>/subchapters/', courses.api_chapter_subchapters_list, name='api_chapter_subchapters_list'),

    # 원페이지 뷰
    path('courses/<int:course_id>/onepage/', courses.course_detail_onepage_view, name='course_detail_onepage'),
    
    # API 엔드포인트 추가
    path('api/chapter/<int:chapter_id>/detail/', courses.api_chapter_detail, name='api_chapter_detail'),
    path('api/subchapter/<int:subchapter_id>/detail/', courses.api_subchapter_detail, name='api_subchapter_detail'),
    path('api/chasi/<int:chasi_id>/detail/', courses.api_chasi_detail, name='api_chasi_detail'),
    path('api/content-types/by-category/<str:category>/', contents_views.api_content_types_by_category, name='api_content_types_by_category'),
    # path('api/chasi/<int:chasi_id>/detail/view/', courses.api_chasi_detail_view, name='api_chasi_detail_view'),
    path('api/course/<int:course_id>/detail/', courses.api_course_detail, name='api_course_detail'),


    # ========================================
    # 차시 관련 API (courses.py)
    # ========================================
    path('api/chasis/<int:chasi_id>/slides/reorder/', courses.api_slide_reorder, name='api_slide_reorder'),
    path('api/chasis/<int:chasi_id>/toggle-publish/', courses.api_toggle_chasi_publish, name='api_toggle_chasi_publish'),
    
    # ========================================
    # 컨텐츠 관련 API (courses.py)
    # ========================================
    # 차시 통합 관리 API
    path('api/contents/list/', chasi_views.api_contents_list, name='api_contents_list'),
    path('api/chasis/<int:chasi_id>/slides/', chasi_views.api_chasi_slides, name='api_chasi_slides'),
    path('api/chasis/<int:chasi_id>/slides/add/', chasi_views.api_slide_add, name='api_slide_add'),
    path('api/slides/<int:slide_id>/delete/', chasi_views.api_slide_delete, name='api_slide_delete'),

    # ★★★ 누락된 콘텐츠 API 추가 ★★★
    path('api/contents/search/', contents_views.api_contents_search, name='api_contents_search'),
    path('api/contents/<int:content_id>/preview/', contents_views.contents_preview, name='contents_preview'),
    path('api/content-types/<int:type_id>/template/', views.api_content_type_template, name='api_content_type_template'),
    path('api/contents/list-with-selected/', chasi_views.api_contents_list_with_selected, name='api_contents_list_with_selected'),
    # urls.py의 콘텐츠 관련 API 섹션에 추가
    path('api/contents/<int:content_id>/detail/', contents_views.api_content_detail, name='api_content_detail'),
]