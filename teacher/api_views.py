# teacher/api_views.py 생성

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import json
from .models import *
@require_http_methods(["GET"])
@login_required
def content_preview_api(request, content_id):
    """콘텐츠 미리보기 API"""
    content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    return JsonResponse({
        'title': content.title,
        'content_type': content.content_type.type_name,
        'page': content.page,
        'answer': content.answer,
        'tags': content.tags,
        'meta_data': content.meta_data,
    })