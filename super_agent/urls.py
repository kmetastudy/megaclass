# cp/urls.py
from django.urls import path
from .views import *

app_name = 'super_agent'

urlpatterns = [
    # 메인 페이지: 파일 업로드 및 문항 트리 뷰
    path('', QuestionAgentView.as_view(), name='index'),
    
    # AJAX 요청을 처리할 URL: 파일 처리 및 문항 생성
    path('process/', process_files, name='process_files'),

    # AJAX 요청을 처리할 URL: 생성된 문항 트리 데이터를 가져옴
    path('get-tree/', get_question_tree, name='get_question_tree'),
  
]