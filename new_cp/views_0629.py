# cp/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views import View
import json,os
import mimetypes
import requests
from .models import Contents_Template
from teacher.models import ContentType, ContentTypeCategory, Course, Chapter, Contents,ContentsAttached
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid


# 메인 페이지
@login_required
def cp_agent_view(request):
    """AI 문항 생성기 메인 페이지"""
    return render(request, 'cp/cp_agent.html')

# API 뷰들
@login_required
def api_categories(request):
    """카테고리 목록 API"""
    categories = ContentTypeCategory.objects.all().values('id', 'category_name', 'description')
    return JsonResponse(list(categories), safe=False)

# cp/views.py의 api_content_types 함수 수정
@login_required
def api_content_types(request):
    """컨텐츠 타입 목록 API"""
    # 카테고리 필터 파라미터 받기
    category_id = request.GET.get('category')
    
    # 기본 쿼리셋
    queryset = ContentType.objects.filter(is_active=True)
    
    # 카테고리 필터링
    if category_id:
        queryset = queryset.filter(category_name_id=category_id)
    
    # select_related로 카테고리 정보도 함께 가져오기
    types = queryset.select_related('category_name').values(
        'id', 
        'type_name', 
        'category_name__id',
        'category_name__category_name', 
        'description'
    )
    
    return JsonResponse(list(types), safe=False)

@login_required
def api_courses(request):
    """코스 목록 API"""
    courses = Course.objects.filter(
        teacher__user=request.user,
        is_active=True
    ).values('id', 'subject_name', 'target', 'description')
    return JsonResponse(list(courses), safe=False)

@login_required
def api_course_chapters(request, course_id):
    """특정 코스의 챕터 목록 API"""
    chapters = Chapter.objects.filter(
        subject_id=course_id
    ).values('id', 'chapter_title', 'chapter_order')
    return JsonResponse(list(chapters), safe=False)

@login_required
def api_contents_search(request):
    """콘텐츠 검색 API"""
    # 검색 파라미터
    category = request.GET.get('category')
    content_type = request.GET.get('type')
    course = request.GET.get('course')
    chapter = request.GET.get('chapter')
    search = request.GET.get('search')
    
    # 기본 쿼리셋
    queryset = Contents.objects.filter(is_active=True)
    
    # 필터링
    if category:
        queryset = queryset.filter(content_type__category_name_id=category)
    if content_type:
        queryset = queryset.filter(content_type_id=content_type)
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | 
            Q(page__icontains=search)
        )
    
    # 코스/챕터 필터링 (차시를 통해)
    if course or chapter:
        from teacher.models import ChasiSlide
        content_ids = ChasiSlide.objects.filter(is_active=True)
        if course:
            content_ids = content_ids.filter(chasi__subject_id=course)
        if chapter:
            content_ids = content_ids.filter(chasi__chapter_id=chapter)
        content_ids = content_ids.values_list('content_id', flat=True).distinct()
        queryset = queryset.filter(id__in=content_ids)
    
    # 결과 정렬 및 제한
    contents = queryset.order_by('-created_at')[:50].values(
        'id', 'title', 'content_type__type_name', 'created_at', 'page'
    )
    
    # 응답 형식 맞추기
    result = []
    for content in contents:
        result.append({
            'id': content['id'],
            'title': content['title'],
            'content_type_name': content['content_type__type_name'],
            'created_at': content['created_at'].strftime('%Y.%m.%d'),
            'preview': content['page'][:100] + '...' if len(content['page']) > 100 else content['page']
        })
    
    return JsonResponse(result, safe=False)

@login_required
def api_templates_search(request):
    """템플릿 검색 API"""
    # 검색 파라미터
    category = request.GET.get('category')
    content_type = request.GET.get('type')
    search = request.GET.get('search')
    
    # 기본 쿼리셋 - Contents_Template 사용
    queryset = Contents_Template.objects.filter(is_active=True, is_public=True)
    
    # 필터링
    if category:
        queryset = queryset.filter(content_category_id=category)
    if content_type:
        queryset = queryset.filter(content_type_id=content_type)
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | 
            Q(page__icontains=search)
        )
    
    # 결과 정렬 및 제한
    templates = queryset.order_by('-created_at')[:50].values(
        'id', 'title', 'content_type__type_name', 'created_at', 
        'page', 'answer', 'meta_data', 'tags'
    )
    
    # 응답 형식 맞추기
    result = []
    for template in templates:
        result.append({
            'id': template['id'],
            'title': template['title'],
            'content_type_name': template['content_type__type_name'],
            'created_at': template['created_at'].strftime('%Y.%m.%d'),
            'page': template['page'],
            'answer': template['answer'],
            'meta_data': template['meta_data'],
            'tags': template['tags']
        })
    
    return JsonResponse(result, safe=False)

@login_required
def api_content_detail(request, content_id):
    """콘텐츠 상세 정보 API"""
    content = get_object_or_404(Contents, id=content_id)
    
    data = {
        'id': content.id,
        'title': content.title,
        'content_type': content.content_type_id,
        'page': content.page,
        'answer': content.answer or '',
        'meta_data': content.meta_data or {},
        'tags': content.tags or {}
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def api_generate_content(request):
    """AI를 사용한 콘텐츠 생성 API"""
    try:
        data = json.loads(request.body)
        
        # Claude API 키 확인
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not api_key:
            return JsonResponse({'error': 'API key not configured'}, status=500)
        
        # 프롬프트 생성
        prompt = create_content_prompt(data)
        
        # Claude API 호출
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        payload = {
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': 4000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': 'AI API error'}, status=500)
        
        # 응답 파싱
        ai_response = response.json()
        content_text = ai_response['content'][0]['text']
        
        # AI 응답을 파싱하여 구조화된 데이터 추출
        result = parse_ai_response(content_text)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def create_content_prompt(data):
    """AI 프롬프트 생성"""
    content_type = ContentType.objects.get(id=data['content_type'])
    
    prompt = f"""
다음 정보를 바탕으로 교육용 문항을 생성해주세요:

제목: {data['title']}
컨텐츠 타입: {content_type.type_name}

{"템플릿 HTML: " + data.get('page', '') if data.get('page') else ""}
{"템플릿 정답: " + data.get('answer', '') if data.get('answer') else ""}

요구사항:
1. HTML은 Tailwind CSS 클래스를 사용하여 아름답게 스타일링해주세요
2. 문항은 명확하고 교육적이어야 합니다
3. 정답은 JSON 형식으로 제공해주세요

응답 형식:
[HTML_START]
(여기에 HTML 코드)
[HTML_END]

[ANSWER_START]
(여기에 JSON 형식의 정답)
[ANSWER_END]

[META_START]
(여기에 메타데이터 JSON - 선택사항)
[META_END]

[TAGS_START]
(여기에 평가기준 JSON - 선택사항)
[TAGS_END]
"""
    
    return prompt

def parse_ai_response(response_text):
    """AI 응답 파싱"""
    result = {
        'page': '',
        'answer': '{}',
        'meta_data': '{}',
        'tags': '{}'
    }
    
    # HTML 추출
    html_match = response_text.split('[HTML_START]')
    if len(html_match) > 1:
        html_end = html_match[1].split('[HTML_END]')
        if len(html_end) > 0:
            result['page'] = html_end[0].strip()
    
    # 정답 추출
    answer_match = response_text.split('[ANSWER_START]')
    if len(answer_match) > 1:
        answer_end = answer_match[1].split('[ANSWER_END]')
        if len(answer_end) > 0:
            result['answer'] = answer_end[0].strip()
    
    # 메타데이터 추출
    meta_match = response_text.split('[META_START]')
    if len(meta_match) > 1:
        meta_end = meta_match[1].split('[META_END]')
        if len(meta_end) > 0:
            result['meta_data'] = meta_end[0].strip()
    
    # 태그 추출
    tags_match = response_text.split('[TAGS_START]')
    if len(tags_match) > 1:
        tags_end = tags_match[1].split('[TAGS_END]')
        if len(tags_end) > 0:
            result['tags'] = tags_end[0].strip()
    
    return result

@login_required
@require_http_methods(["POST"])
def api_contents_create(request):
    """콘텐츠 생성 API"""
    try:
        data = json.loads(request.body)
        
        # 콘텐츠 생성
        content = Contents.objects.create(
            title=data['title'],
            content_type_id=data['content_type'],
            page=data['page'],
            answer=data.get('answer', ''),
            meta_data=json.loads(data.get('meta_data', '{}')),
            tags=json.loads(data.get('tags', '{}')),
            created_by=request.user,
            is_active=True,
            is_public=True
        )
        
        return JsonResponse({
            'id': content.id,
            'title': content.title,
            'created_at': content.created_at.strftime('%Y.%m.%d')
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["PUT"])
def api_contents_update(request, content_id):
    """콘텐츠 수정 API"""
    try:
        data = json.loads(request.body)
        content = get_object_or_404(Contents, id=content_id)
        
        # 권한 확인
        if content.created_by != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # 업데이트
        content.title = data['title']
        content.content_type_id = data['content_type']
        content.page = data['page']
        content.answer = data.get('answer', '')
        content.meta_data = json.loads(data.get('meta_data', '{}'))
        content.tags = json.loads(data.get('tags', '{}'))
        content.save()
        
        return JsonResponse({
            'id': content.id,
            'title': content.title,
            'updated_at': content.updated_at.strftime('%Y.%m.%d')
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def api_templates_create(request):
    """템플릿 생성 API"""
    try:
        data = json.loads(request.body)
        
        # 템플릿 생성
        template = Contents_Template.objects.create(
            title=data['title'],
            content_category_id=data['content_category'],
            content_type_id=data['content_type'],
            page=data['page'],
            answer=data.get('answer', ''),
            meta_data=json.loads(data.get('meta_data', '{}')),
            tags=json.loads(data.get('tags', '{}')),  # JS 코드를 tags에 저장
            created_by=request.user,
            is_active=True,
            is_public=data.get('is_public', True)
        )
        
        return JsonResponse({
            'id': template.id,
            'title': template.title,
            'created_at': template.created_at.strftime('%Y.%m.%d')
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

# 첨부 파일 이미지 업로드
@login_required
@require_http_methods(["POST"])
def upload_image(request):
    """이미지 업로드 API"""
    try:
        # 파일 검증
        if 'file' not in request.FILES:
            return JsonResponse({'error': '파일이 없습니다.'}, status=400)
        
        file = request.FILES['file']
        original_name = request.POST.get('original_name', file.name)
        file_type = request.POST.get('file_type', file.content_type)
        file_size = request.POST.get('file_size', file.size)
        content_id = request.POST.get('content_id')
        
        # 파일 크기 검증 (10MB)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': '파일 크기는 10MB 이하여야 합니다.'}, status=400)
        
        # 파일 타입 검증
        if not file.content_type.startswith('image/'):
            return JsonResponse({'error': '이미지 파일만 업로드 가능합니다.'}, status=400)
        
        # 고유한 파일명 생성
        file_extension = os.path.splitext(original_name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # 파일 저장
        file_path = f"contents/attachments/{request.user.id}/{unique_filename}"
        saved_path = default_storage.save(file_path, ContentFile(file.read()))
        
        # ContentsAttached 객체 생성
        attachment = ContentsAttached.objects.create(
            contents_id=content_id if content_id else None,  # content_id가 있으면 연결, 없으면 임시 파일
            file=saved_path,
            original_name=original_name,
            file_type=file_type,
            file_size=int(file_size),
            uploaded_by=request.user,
            is_temporary=True if not content_id else False
        )
        
        return JsonResponse({
            'success': True,
            'attachment_id': attachment.id,
            'file_url': default_storage.url(saved_path),
            'original_name': original_name,
            'file_size': file_size
        })
        
    except Exception as e:
        return JsonResponse({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
@require_http_methods(["DELETE"])
def cleanup_temp_upload(request, attachment_id):
    """임시 업로드 파일 정리"""
    try:
        attachment = get_object_or_404(
            ContentsAttached, 
            id=attachment_id, 
            uploaded_by=request.user,
            is_temporary=True
        )
        
        # 파일 삭제
        if attachment.file:
            default_storage.delete(attachment.file.name)
        
        # DB 레코드 삭제
        attachment.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': f'파일 정리 중 오류가 발생했습니다: {str(e)}'}, status=500)







@require_http_methods(["POST"])
def upload_image_o62818(request):
    """
    이미지 임시 업로드 API
    
    POST /cp/api/upload-image/
    Content-Type: multipart/form-data
    
    Parameters:
    - file: 업로드할 이미지 파일
    - original_name: 원본 파일명
    - file_type: 파일 MIME 타입
    - file_size: 파일 크기 (bytes)
    - content_id: 연결할 콘텐츠 ID (선택사항)
    """
    try:
        # 파일 검증
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({
                'error': '파일이 선택되지 않았습니다.'
            }, status=400)
        
        # 파일 크기 검증 (10MB 제한)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return JsonResponse({
                'error': f'파일 크기는 {max_size // (1024*1024)}MB 이하여야 합니다.'
            }, status=400)
        
        # 파일 타입 검증
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        file_type = request.POST.get('file_type', file.content_type)
        
        if file_type not in allowed_types:
            return JsonResponse({
                'error': '지원하지 않는 이미지 형식입니다. (JPG, PNG, GIF, WebP만 허용)'
            }, status=400)
        
        # 콘텐츠 ID 검증 (있는 경우만)
        content_id = request.POST.get('content_id')
        contents_instance = None
        
        if content_id:
            try:
                contents_instance = Contents.objects.get(id=content_id, teacher=request.user)
            except Contents.DoesNotExist:
                return JsonResponse({
                    'error': '해당 콘텐츠를 찾을 수 없거나 권한이 없습니다.'
                }, status=404)
        
        # ContentsAttached 모델에 임시 저장
        attachment = ContentsAttached.objects.create(
            contents=contents_instance,  # None일 수 있음 (임시 업로드)
            file=file,
            original_name=request.POST.get('original_name', file.name),
            file_type=file_type,
            file_size=int(request.POST.get('file_size', file.size))
        )
        
        # 성공 응답
        return JsonResponse({
            'success': True,
            'attachment_id': attachment.id,
            'file_url': attachment.file.url,
            'original_name': attachment.original_name,
            'file_size': attachment.file_size,
            'uploaded_at': attachment.uploaded_at.isoformat()
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'error': f'이미지 업로드 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def cleanup_temp_upload_062818(request, attachment_id):
    """
    임시 업로드 파일 삭제 API
    
    DELETE /cp/api/cleanup-temp-upload/{attachment_id}/
    
    Parameters:
    - attachment_id: 삭제할 첨부파일 ID
    """
    try:
        # 첨부파일 조회 (권한 확인 포함)
        attachment = ContentsAttached.objects.get(id=attachment_id)
        
        # 권한 확인: 콘텐츠가 있는 경우 소유자 확인, 없는 경우(임시 파일) 그냥 삭제
        if attachment.contents and attachment.contents.teacher != request.user:
            return JsonResponse({
                'error': '해당 파일을 삭제할 권한이 없습니다.'
            }, status=403)
        
        # 실제 파일 삭제
        if attachment.file:
            try:
                # 파일 시스템에서 물리적 삭제
                if default_storage.exists(attachment.file.name):
                    default_storage.delete(attachment.file.name)
            except Exception as file_error:
                print(f"파일 삭제 오류: {file_error}")
                # 파일 삭제 실패해도 DB 레코드는 삭제 진행
        
        # DB에서 레코드 삭제
        attachment_info = {
            'id': attachment.id,
            'original_name': attachment.original_name
        }
        attachment.delete()
        
        return JsonResponse({
            'success': True,
            'message': '파일이 성공적으로 삭제되었습니다.',
            'deleted_file': attachment_info
        }, status=200)
        
    except ContentsAttached.DoesNotExist:
        return JsonResponse({
            'error': '삭제할 파일을 찾을 수 없습니다.'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'error': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def list_content_attachments(request, content_id):
    """
    특정 콘텐츠의 첨부파일 목록 조회 API (선택사항)
    
    GET /cp/api/contents/{content_id}/attachments/
    """
    try:
        # 콘텐츠 권한 확인
        content = get_object_or_404(Contents, id=content_id, teacher=request.user)
        
        # 첨부파일 목록 조회
        attachments = ContentsAttached.objects.filter(contents=content).order_by('-uploaded_at')
        
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                'id': attachment.id,
                'file_url': attachment.file.url,
                'original_name': attachment.original_name,
                'file_type': attachment.file_type,
                'file_size': attachment.file_size,
                'uploaded_at': attachment.uploaded_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'content_id': content_id,
            'attachments': attachment_list,
            'total_count': len(attachment_list)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'error': f'첨부파일 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

    
# @method_decorator([login_required, csrf_exempt], name='dispatch')
# class ImageUploadView(View):
#     """이미지 업로드 API"""
    
#     def post(self, request):
#         try:
#             # 파일 확인
#             if 'file' not in request.FILES:
#                 return JsonResponse({'error': '파일이 없습니다.'}, status=400)
            
#             file = request.FILES['file']
            
#             # 파일 타입 확인 (이미지만 허용)
#             allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
#             if file.content_type not in allowed_types:
#                 return JsonResponse({'error': '지원하지 않는 파일 형식입니다. (jpg, png, gif, webp만 가능)'}, status=400)
            
#             # 파일 크기 확인 (10MB 제한)
#             max_size = 10 * 1024 * 1024  # 10MB
#             if file.size > max_size:
#                 return JsonResponse({'error': '파일 크기가 너무 큽니다. (10MB 이하만 가능)'}, status=400)
            
#             # 원본 파일명과 기타 정보
#             original_name = request.POST.get('original_name', file.name)
#             file_type = request.POST.get('file_type', file.content_type)
#             file_size = int(request.POST.get('file_size', file.size))
#             content_id = request.POST.get('content_id')
            
#             # ContentsAttached 객체 생성
#             attachment = ContentsAttached(
#                 original_name=original_name,
#                 file_type=file_type,
#                 file_size=file_size,
#             )
            
#             # 콘텐츠 ID가 있으면 연결 (저장된 콘텐츠의 경우)
#             if content_id and content_id.isdigit():
#                 try:
#                     contents = Contents.objects.get(id=content_id, created_by=request.user)
#                     attachment.contents = contents
#                 except Contents.DoesNotExist:
#                     return JsonResponse({'error': '콘텐츠를 찾을 수 없습니다.'}, status=404)
            
#             # 파일 저장
#             attachment.file = file
#             attachment.save()
            
#             # 파일 URL 생성
#             file_url = request.build_absolute_uri(attachment.file.url)
            
#             return JsonResponse({
#                 'success': True,
#                 'file_url': file_url,
#                 'attachment_id': attachment.id,
#                 'original_name': original_name,
#                 'file_size': file_size,
#                 'message': '이미지가 성공적으로 업로드되었습니다.'
#             })
            
#         except Exception as e:
#             print(f"이미지 업로드 오류: {str(e)}")
#             return JsonResponse({'error': f'서버 오류가 발생했습니다: {str(e)}'}, status=500)

# @login_required
# @require_http_methods(["DELETE"])
# def cleanup_temp_upload(request, attachment_id):
#     """임시 업로드 파일 정리 API"""
#     try:
#         # 첨부파일 찾기
#         attachment = ContentsAttached.objects.get(id=attachment_id)
        
#         # 권한 확인 (콘텐츠가 없거나 작성자가 같은 경우만 삭제 가능)
#         if attachment.contents and attachment.contents.created_by != request.user:
#             return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
#         # 파일 삭제
#         if attachment.file:
#             try:
#                 # 실제 파일 삭제
#                 if default_storage.exists(attachment.file.name):
#                     default_storage.delete(attachment.file.name)
#                     print(f"파일 삭제 완료: {attachment.file.name}")
#             except Exception as e:
#                 print(f"파일 삭제 오류: {str(e)}")
        
#         # 데이터베이스에서 삭제
#         attachment.delete()
        
#         return JsonResponse({
#             'success': True,
#             'message': '임시 파일이 삭제되었습니다.'
#         })
        
#     except ContentsAttached.DoesNotExist:
#         return JsonResponse({'error': '파일을 찾을 수 없습니다.'}, status=404)
#     except Exception as e:
#         print(f"임시 파일 삭제 오류: {str(e)}")
#         return JsonResponse({'error': f'서버 오류가 발생했습니다: {str(e)}'}, status=500)