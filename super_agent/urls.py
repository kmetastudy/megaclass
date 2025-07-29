# cp/urls.py
from django.urls import path
from .views import *
from .batch import *
from .course_designer_views import *

app_name = 'super_agent'

urlpatterns = [
    # ========================================
    # 메인 페이지
    # ========================================
    path('', agent_main_view, name='agent_main'),
    
    # ========================================
    # 코스 관련 API
    # ========================================
    path('api/courses/search/', api_course_search, name='api_course_search'),
    path('api/courses/<int:course_id>/structure/', api_course_structure, name='api_course_structure'),
    path('api/courses/<int:course_id>/structure/update/', api_course_structure_update, name='api_course_structure_update'),
    
    # ========================================
    # 콘텐츠 관련 API
    # ========================================
    path('api/contents/create/', api_content_create_with_prompt, name='api_content_create_with_prompt'),
    path('api/contents/<int:content_id>/update/', api_content_update_with_prompt, name='api_content_update_with_prompt'),
    path('api/contents/search/', api_content_search, name='api_content_search'),
    path('api/contents/<int:content_id>/detail/', api_content_detail, name='api_content_detail'),
    
    # ========================================
    # 통계 및 분석 API
    # ========================================
    path('api/statistics/', api_agent_statistics, name='api_agent_statistics'),


    ###### 구 파일들 #######################################
    #path('',dashboard_view,name='dashboard'),
    # 메인 페이지: 파일 업로드 및 문항 트리 뷰
    path('questions/', QuestionAgentView.as_view(), name='index'),
    path('api/courses/structure/', api_courses_structure, name='api_courses_structure'),
    
    # 새로 추가할 배치 처리 URL
    path('questions/batch/', batch_process_view, name='batch_process'),
    path('api/questions/batch/upload/', api_batch_upload, name='api_batch_upload'),
    path('api/questions/batch/process/', api_batch_process_item, name='api_batch_process_item'),
    path('api/questions/batch/status/', api_processing_status, name='api_processing_status'),
    path('api/contents/batch/<int:content_id>/update/', api_content_update, name='api_content_update'),
    
   
    # 슬라이드 미리보기 API (새로 추가)
    path('api/slides/<int:slide_id>/preview/', api_slide_preview, name='api_slide_preview'),
    path('api/slides/<int:slide_id>/update/', api_slide_update, name='api_slide_update'), #  <- Add this line

    # ========================================
    # 파일 관리 API (새로 추가)
    # ========================================
    path('api/files/upload/temporary/', api_upload_temporary_file, name='api_upload_temporary_file'),
    path('api/files/delete/temporary/', api_delete_temporary_file, name='api_delete_temporary_file'),
    path('api/contents/<int:content_id>/attachments/finalize/', api_finalize_attachments, name='api_finalize_attachments'),

    # AJAX 요청을 처리할 URL: 파일 처리 및 문항 생성
    path('process/', process_files, name='process_files'),

    # AJAX 요청을 처리할 URL: 생성된 문항 트리 데이터를 가져옴
    path('get-tree/', get_question_tree, name='get_question_tree'),

    # ====================================================================================
    # 코스 및 컨텐츠 디자이너 
    # ====================================================================================
    # ... 기존 URL 패턴들 ...
    
    # 코스 설계 API
    path('api/course-designer/design/', 
         design_course_structure, 
         name='api_design_course_structure'),
    # path('api/course-designer/preview/', 
    #      preview_course_structure, 
    #      name='api_preview_course_structure'),
         # urls.py에 추가
    path('api/course-designer/design/stream/', 
        design_course_structure_stream, 
        name='api_design_course_structure_stream'),
  
]