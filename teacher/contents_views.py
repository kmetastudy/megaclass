# teacher/views/contents_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
import json
from .decorators import teacher_required

from .models import Contents, ContentType,ChasiSlide
from .forms import ContentsForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

@login_required
def contents_list(request):
    """콘텐츠 목록"""
    # 기본 쿼리셋 - 현재 사용자가 생성한 콘텐츠만
    queryset = Contents.objects.filter(created_by=request.user)
    
    # 콘텐츠 타입 필터
    content_type = request.GET.get('type')
    if content_type:
        queryset = queryset.filter(content_type_id=content_type)
    
    # 검색
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | 
            Q(page__icontains=search)
        )
    
    # select_related로 쿼리 최적화
    queryset = queryset.select_related('content_type').order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(queryset, 20)  # 페이지당 20개
    page = request.GET.get('page')
    contents = paginator.get_page(page)
    
    context = {
        'contents': contents,
        'content_types': ContentType.objects.filter(is_active=True),
        'selected_type': content_type,
        'search_query': search or '',
        'page_obj': contents,
        'is_paginated': paginator.num_pages > 1,
    }
    
    return render(request, 'teacher/contents/list.html', context)

# contents_views.py의 contents_create 함수를 다음으로 수정

import logging
import traceback

logger = logging.getLogger(__name__)

# contents_views.py
import json
import traceback
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

@login_required
@teacher_required
def contents_create(request):
    """콘텐츠 생성 - AJAX 및 일반 요청 지원"""
    # 디버깅 로그
    print(f"\n===== Contents Create =====")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With')}")
    
    from_chasi_id = request.GET.get('from_chasi')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
            # AJAX 요청인 경우 - FormData 직접 처리
            if is_ajax:
                # FormData에서 직접 데이터 추출
                title = request.POST.get('title', '').strip()
                content_type_id = request.POST.get('content_type', '')
                page = request.POST.get('page', '').strip()
                answer = request.POST.get('answer', '').strip()
                meta_data_str = request.POST.get('meta_data', '{}')
                tags_str = request.POST.get('tags', '{}')
                
                print(f"Received data - Title: {title}, Type: {content_type_id}")
                
                # 기본 검증
                if not title:
                    return JsonResponse({'error': '제목을 입력해주세요.'}, status=400)
                if not content_type_id:
                    return JsonResponse({'error': '콘텐츠 타입을 선택해주세요.'}, status=400)
                if not page:
                    return JsonResponse({'error': '내용을 입력해주세요.'}, status=400)
                
                # ContentType 확인
                try:
                    content_type = ContentType.objects.get(id=content_type_id, is_active=True)
                except ContentType.DoesNotExist:
                    return JsonResponse({'error': '유효하지 않은 콘텐츠 타입입니다.'}, status=400)
                
                # JSON 파싱
                try:
                    meta_data = json.loads(meta_data_str) if meta_data_str else {}
                    tags = json.loads(tags_str) if tags_str else {}
                except json.JSONDecodeError as e:
                    return JsonResponse({'error': f'JSON 파싱 오류: {str(e)}'}, status=400)
                
                # 콘텐츠 생성
                content = Contents.objects.create(
                    title=title,
                    content_type=content_type,
                    page=page,
                    answer=answer if answer else '',
                    meta_data=meta_data,
                    tags=tags,
                    created_by=request.user,
                    is_active=True,
                    is_public=request.POST.get('is_public', '') == 'on'
                )
                
                print(f"Content created with ID: {content.id}")
                
                return JsonResponse({
                    'success': True,
                    'message': '콘텐츠가 생성되었습니다.',
                    'content_id': content.id,
                    'title': content.title
                })
            
            # 일반 폼 요청 처리
            else:
                form = ContentsForm(request.POST)
                if form.is_valid():
                    content = form.save(commit=False)
                    content.created_by = request.user
                    
                    # JSON 필드 처리
                    meta_data = form.cleaned_data.get('meta_data', '{}')
                    tags = form.cleaned_data.get('tags', '{}')
                    
                    content.meta_data = json.loads(meta_data) if meta_data and meta_data.strip() else {}
                    content.tags = json.loads(tags) if tags and tags.strip() else {}
                    
                    content.save()
                    
                    messages.success(request, '콘텐츠가 생성되었습니다.')
                    if from_chasi_id:
                        return redirect('teacher:chasi_slide_add', chasi_id=from_chasi_id)
                    return redirect('teacher:contents_list')
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            
            if is_ajax:
                return JsonResponse({
                    'error': f'처리 중 오류가 발생했습니다: {str(e)}',
                    'error_type': type(e).__name__
                }, status=500)
            
            messages.error(request, f'처리 중 오류가 발생했습니다: {str(e)}')
    
    # GET 요청
    form = ContentsForm()
    context = {
        'form': form,
        'content_types': ContentType.objects.filter(is_active=True),
        'from_chasi_id': from_chasi_id,
    }
    
    return render(request, 'teacher/contents/create.html', context)

@login_required
@teacher_required
@csrf_protect
def contents_create_062222(request):
    """콘텐츠 생성 - AJAX 및 일반 요청 지원"""
    # 디버깅을 위한 로그
    print(f"\n===== Contents Create Debug =====")
    print(f"Method: {request.method}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With')}")
    print(f"Content-Type: {request.content_type}")
    print(f"POST keys: {list(request.POST.keys())}")
    print(f"User: {request.user}")
    print("=================================\n")
    
    from_chasi_id = request.GET.get('from_chasi')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
            # POST 데이터 확인
            print(f"POST data: {dict(request.POST)}")
            
            # FormData로 전송된 경우 처리
            form_data = request.POST.copy()
            
            # meta_data와 tags가 JSON 문자열로 전송된 경우 파싱
            if 'meta_data' in form_data and form_data['meta_data']:
                try:
                    # 이미 dict인지 확인
                    if isinstance(form_data['meta_data'], dict):
                        meta_data_parsed = form_data['meta_data']
                    else:
                        meta_data_parsed = json.loads(form_data['meta_data'])
                    print(f"Parsed meta_data: {meta_data_parsed}")
                except json.JSONDecodeError as e:
                    print(f"Meta data JSON error: {e}")
                    if is_ajax:
                        return JsonResponse({'error': 'meta_data JSON 파싱 오류'}, status=400)
            
            if 'tags' in form_data and form_data['tags']:
                try:
                    if isinstance(form_data['tags'], dict):
                        tags_parsed = form_data['tags']
                    else:
                        tags_parsed = json.loads(form_data['tags'])
                    print(f"Parsed tags: {tags_parsed}")
                except json.JSONDecodeError as e:
                    print(f"Tags JSON error: {e}")
                    if is_ajax:
                        return JsonResponse({'error': 'tags JSON 파싱 오류'}, status=400)
            
            # 폼 생성
            form = ContentsForm(form_data)
            
            if form.is_valid():
                print("Form is valid")
                content = form.save(commit=False)
                content.created_by = request.user
                
                # JSON 필드 처리
                try:
                    # meta_data 처리
                    meta_data_str = form.cleaned_data.get('meta_data', '{}')
                    if not meta_data_str or meta_data_str.strip() == '':
                        content.meta_data = {}
                    else:
                        content.meta_data = json.loads(meta_data_str) if isinstance(meta_data_str, str) else meta_data_str
                    
                    # tags 처리
                    tags_str = form.cleaned_data.get('tags', '{}')
                    if not tags_str or tags_str.strip() == '':
                        content.tags = {}
                    else:
                        content.tags = json.loads(tags_str) if isinstance(tags_str, str) else tags_str
                    
                    # 콘텐츠 저장
                    content.save()
                    print(f"Content saved with ID: {content.id}")
                    
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'message': '콘텐츠가 생성되었습니다.',
                            'content_id': content.id,
                            'title': content.title
                        })
                    
                    messages.success(request, '콘텐츠가 생성되었습니다.')
                    if from_chasi_id:
                        return redirect('teacher:chasi_slide_add', chasi_id=from_chasi_id)
                    return redirect('teacher:contents_list')
                    
                except Exception as e:
                    print(f"Save error: {type(e).__name__}: {str(e)}")
                    print(traceback.format_exc())
                    
                    if is_ajax:
                        return JsonResponse({
                            'error': f'저장 중 오류: {str(e)}'
                        }, status=500)
                    
                    messages.error(request, f'저장 중 오류가 발생했습니다: {str(e)}')
            
            else:
                # 폼 검증 실패
                print(f"Form errors: {form.errors}")
                print(f"Form data: {form.data}")
                
                if is_ajax:
                    errors = {}
                    for field, error_list in form.errors.items():
                        errors[field] = [str(error) for error in error_list]
                    return JsonResponse({'errors': errors, 'success': False}, status=400)
        
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            
            if is_ajax:
                return JsonResponse({
                    'error': f'처리 중 오류: {str(e)}',
                    'error_type': type(e).__name__
                }, status=500)
            
            messages.error(request, f'처리 중 오류가 발생했습니다: {str(e)}')
    
    # GET 요청 처리
    form = ContentsForm()
    context = {
        'form': form,
        'content_types': ContentType.objects.filter(is_active=True),
        'from_chasi_id': from_chasi_id,
    }
    
    return render(request, 'teacher/contents/create.html', context)

@login_required
@teacher_required
def contents_create_062217(request):
    """콘텐츠 생성 - AJAX 및 일반 요청 지원"""
    """콘텐츠 생성 - AJAX 및 일반 요청 지원"""
    logger.debug(f"Contents create called - Method: {request.method}")
    logger.debug(f"Is AJAX: {request.headers.get('X-Requested-With')}")
    logger.debug(f"POST data: {request.POST}")
    # 차시에서 왔는지 확인
    from_chasi_id = request.GET.get('from_chasi')
    
    if request.method == 'POST':
        # AJAX 요청인지 확인
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        form = ContentsForm(request.POST)
        if form.is_valid():
            try:
                content = form.save(commit=False)
                content.created_by = request.user
                
                # JSON 필드 처리
                meta_data = form.cleaned_data.get('meta_data', '{}')
                if not meta_data or meta_data.strip() == '':
                    content.meta_data = {}
                else:
                    content.meta_data = json.loads(meta_data)
                
                tags = form.cleaned_data.get('tags', '{}')
                if not tags or tags.strip() == '':
                    content.tags = {}
                else:
                    content.tags = json.loads(tags)
                
                content.save()
                
                # AJAX 응답
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': '콘텐츠가 생성되었습니다.',
                        'content_id': content.id,
                        'title': content.title
                    })
                
                # 일반 응답
                messages.success(request, '콘텐츠가 생성되었습니다.')
                if from_chasi_id:
                    return redirect('teacher:chasi_slide_add', chasi_id=from_chasi_id)
                return redirect('teacher:contents_list')
                
            except json.JSONDecodeError as e:
                error_msg = f'JSON 형식 오류: {str(e)}'
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=400)
                
                messages.error(request, error_msg)
                
            except Exception as e:
                error_msg = f'콘텐츠 생성 중 오류: {str(e)}'
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=500)
                
                messages.error(request, error_msg)
        
        else:
            # 폼 검증 실패
            if is_ajax:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse(errors, status=400)
            
            # 일반 요청인 경우 폼 에러와 함께 다시 렌더링
            
    else:
        form = ContentsForm()
    
    context = {
        'form': form,
        'content_types': ContentType.objects.filter(is_active=True),
        'from_chasi_id': from_chasi_id,
    }
    
    return render(request, 'teacher/contents/create.html', context)


@login_required
def contents_create_0615(request):
    # AJAX 요청 처리
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            form = ContentsForm(request.POST)
            if form.is_valid():
                try:
                    content = form.save(commit=False)
                    content.created_by = request.user
                    
                    # JSON 필드 처리
                    meta_data = form.cleaned_data.get('meta_data', '{}')
                    tags = form.cleaned_data.get('tags', '{}')
                    
                    content.meta_data = json.loads(meta_data) if meta_data else {}
                    content.tags = json.loads(tags) if tags else {}
                    
                    content.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': '콘텐츠가 생성되었습니다.',
                        'content_id': content.id,
                        'title': content.title
                    })
                    
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'JSON 형식 오류'
                    }, status=400)
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    }, status=500)
            else:
                # 폼 검증 오류
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse(errors, status=400)
    """콘텐츠 생성"""
    # 차시에서 왔는지 확인
    from_chasi_id = request.GET.get('from_chasi')
    
    if request.method == 'POST':
        form = ContentsForm(request.POST)
        if form.is_valid():
            content = form.save(commit=False)
            content.created_by = request.user
            
            # JSON 필드 처리
            try:
                # meta_data 처리
                meta_data = form.cleaned_data.get('meta_data', '{}')
                if not meta_data or meta_data.strip() == '':
                    content.meta_data = {}
                else:
                    content.meta_data = json.loads(meta_data)
                
                # tags 처리
                tags = form.cleaned_data.get('tags', '{}')
                if not tags or tags.strip() == '':
                    content.tags = {}
                else:
                    content.tags = json.loads(tags)
                    
            except json.JSONDecodeError as e:
                messages.error(request, f'JSON 형식 오류: {str(e)}')
                return render(request, 'teacher/contents/create.html', {
                    'form': form,
                    'from_chasi_id': from_chasi_id
                })
            
            content.save()
            messages.success(request, '콘텐츠가 생성되었습니다.')
            
            # 차시에서 왔으면 다시 차시로
            if from_chasi_id:
                return redirect('teacher:chasi_slide_add', chasi_id=from_chasi_id)
            
            return redirect('teacher:contents_list')
    else:
        form = ContentsForm()
    
    context = {
        'form': form,
        'content_types': ContentType.objects.filter(is_active=True),
        'from_chasi_id': from_chasi_id,
    }
    
    return render(request, 'teacher/contents/create.html', context)

@login_required
def contents_edit(request, content_id):
    """콘텐츠 수정"""
    content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ContentsForm(request.POST, instance=content)
        if form.is_valid():
            # JSON 필드 처리
            try:
                meta_data = form.cleaned_data.get('meta_data', '{}')
                if not meta_data or meta_data.strip() == '':
                    content.meta_data = {}
                else:
                    content.meta_data = json.loads(meta_data)
                
                tags = form.cleaned_data.get('tags', '{}')
                if not tags or tags.strip() == '':
                    content.tags = {}
                else:
                    content.tags = json.loads(tags)
                    
            except json.JSONDecodeError as e:
                messages.error(request, f'JSON 형식 오류: {str(e)}')
                return render(request, 'teacher/contents/edit.html', {
                    'form': form,
                    'object': content
                })
            
            form.save()
            messages.success(request, '콘텐츠가 수정되었습니다.')
            return redirect('teacher:contents_list')
    else:
        # 기존 JSON 데이터를 문자열로 변환
        initial_data = {
            'meta_data': json.dumps(content.meta_data, ensure_ascii=False) if content.meta_data else '{}',
            'tags': json.dumps(content.tags, ensure_ascii=False) if content.tags else '{}'
        }
        form = ContentsForm(instance=content, initial=initial_data)
    
    context = {
        'form': form,
        'object': content,
        'content': content,
        'content_types': ContentType.objects.filter(is_active=True),
    }
    
    return render(request, 'teacher/contents/edit.html', context)

@login_required
@require_POST
def contents_delete(request, content_id):
    """콘텐츠 삭제"""
    content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    # 이 콘텐츠를 사용하는 슬라이드가 있는지 확인
    slide_count = content.chasislide_set.count()
    if slide_count > 0:
        messages.error(
            request, 
            f'이 콘텐츠는 {slide_count}개의 슬라이드에서 사용 중이므로 삭제할 수 없습니다.'
        )
        return redirect('teacher:contents_list')
    
    content_title = content.title
    content.delete()
    messages.success(request, f'"{content_title}" 콘텐츠가 삭제되었습니다.')
    
    return redirect('teacher:contents_list')

@login_required
def contents_preview(request, content_id):
    """콘텐츠 미리보기 API"""
    # content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    content = get_object_or_404(Contents, id=content_id)
    
    data = {
        'title': content.title,
        'content_type': content.content_type.type_name,
        'page': content.page,
        'answer': content.answer,
        'tags': content.tags,
        'meta_data': content.meta_data
    }
    
    return JsonResponse(data)


@login_required
def contents_duplicate(request, content_id):
    """콘텐츠 복제"""
    original = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    # 콘텐츠 복제
    duplicated = Contents.objects.create(
        content_type=original.content_type,
        title=f"{original.title} (복사본)",
        page=original.page,
        answer=original.answer,
        meta_data=original.meta_data,
        tags=original.tags,
        created_by=request.user
    )
    
    messages.success(request, f'"{original.title}" 콘텐츠가 복제되었습니다.')
    
    # return_to 파라미터 확인
    return_to = request.GET.get('return_to')
    slide_id = request.GET.get('slide_id')
    
    if return_to == 'slide_edit' and slide_id:
        # 슬라이드 편집 페이지로 돌아가면서 새 콘텐츠 선택
        slide = get_object_or_404(ChasiSlide, id=slide_id)
        slide.content = duplicated
        slide.save()
        return redirect('teacher:chasi_slide_edit', slide_id=slide_id)
    
    return redirect('teacher:contents_edit', content_id=duplicated.id)


# contents_views.py에 추가할 함수

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .decorators import teacher_required

### 여러개의 컨텐츠를 검색하여 요청
@login_required
@teacher_required
def api_contents_search(request):
    """콘텐츠 검색 API"""
    try:
        teacher = request.user.teacher
        
        # 검색 파라미터 가져오기
        query = request.GET.get('q', '').strip()
        content_type_id = request.GET.get('content_type', '')
        chapter_search = request.GET.get('chapter', '').strip()  # ID 대신 제목 검색어
        course_id = request.GET.get('course_id', '')
        chasi_id = request.GET.get('chasi_id', '')  # 차시 ID 추가
        
        print(f"\n===== 콘텐츠 검색 시작 =====")
        print(f"요청 사용자: {request.user.username} (ID: {request.user.id})")
        print(f"검색 파라미터:")
        print(f"  - query: '{query}'")
        print(f"  - content_type_id: '{content_type_id}'")
        print(f"  - chapter_search: '{chapter_search}'")
        print(f"  - course_id: '{course_id}'")
        print(f"  - chasi_id: '{chasi_id}'")
        print(f"===========================")
        
        # 단계별 카운트 저장
        step_counts = {}
        
        # 기본 쿼리셋 (활성화된 콘텐츠만)
        contents = Contents.objects.filter(is_active=True)
        step_counts['step1'] = contents.count()
        print(f"\n[1단계] 활성화된 콘텐츠: {step_counts['step1']}개")
        
        # 현재 교사가 생성한 콘텐츠 또는 공개 콘텐츠
        contents = contents.filter(
            Q(created_by=request.user) | Q(is_public=True)
        )
        step_counts['step2'] = contents.count()
        print(f"[2단계] 권한 필터 후 (created_by={request.user.id} OR is_public=True): {step_counts['step2']}개")
        
        # 차시 필터 (최우선 적용)
        if chasi_id:
            before_count = contents.count()
            contents = contents.filter(
                chasislide__chasi_id=chasi_id
            ).distinct()
            step_counts['step_chasi'] = contents.count()
            print(f"[3단계] 차시 필터 (chasi_id={chasi_id}) 적용: {before_count}개 → {step_counts['step_chasi']}개")
        else:
            print(f"[3단계] 차시 필터 없음")
        
        # 텍스트 검색
        if query:
            before_count = contents.count()
            contents = contents.filter(
                Q(title__icontains=query) |
                Q(page__icontains=query)
            )
            step_counts['step3'] = contents.count()
            print(f"[4단계] 텍스트 검색 '{query}' 적용: {before_count}개 → {step_counts['step3']}개")
        else:
            print(f"[4단계] 텍스트 검색 없음")
        
        # 콘텐츠 타입 필터
        if content_type_id:
            before_count = contents.count()
            contents = contents.filter(content_type_id=content_type_id)
            step_counts['step4'] = contents.count()
            print(f"[5단계] 콘텐츠 타입 필터 (type_id={content_type_id}) 적용: {before_count}개 → {step_counts['step4']}개")
        else:
            print(f"[5단계] 콘텐츠 타입 필터 없음")
        
        # 코스 필터링
        # if course_id and not chasi_id:
        #     before_count = contents.count()
        #     contents = contents.filter(
        #         chasislide__chasi__subject_id=course_id
        #     ).distinct()
        #     step_counts['step5'] = contents.count()
        #     print(f"[6단계] 코스 필터 (course_id={course_id}) 적용: {before_count}개 → {step_counts['step5']}개")
        # else:
        #     print(f"[6단계] 코스 필터 없음")
        
        # 대단원 제목으로 필터링
        if chapter_search and not chasi_id:
            before_count = contents.count()
            contents = contents.filter(
                chasislide__chasi__chapter__chapter_title__icontains=chapter_search
            ).distinct()
            step_counts['step6'] = contents.count()
            print(f"[7단계] 대단원 제목 필터 '{chapter_search}' 적용: {before_count}개 → {step_counts['step6']}개")
        else:
            print(f"[7단계] 대단원 필터 없음")
        
        # 정렬 및 제한
        total_before_limit = contents.count()
        contents = contents.select_related(
            'content_type', 'created_by'
        ).order_by('-created_at')[:50]
        
        print(f"\n[최종] 필터링 완료")
        print(f"  - 제한 전: {total_before_limit}개")
        print(f"  - 제한 후 (최대 50개): {len(contents)}개")
        
        # 결과 직렬화
        results = []
        for idx, content in enumerate(contents):
            # 미리보기 텍스트 생성
            preview = content.get_preview() if hasattr(content, 'get_preview') else ''
            
            # 이 콘텐츠가 사용된 첫 번째 슬라이드를 통해 대단원/소단원 정보 가져오기
            first_slide = content.chasislide_set.select_related(
                'chasi__chapter', 'chasi__sub_chapter'
            ).first()
            
            chapter_name = ''
            subchapter_name = ''
            if first_slide:
                if first_slide.chasi.chapter:
                    chapter_name = first_slide.chasi.chapter.chapter_title
                if first_slide.chasi.sub_chapter:
                    subchapter_name = first_slide.chasi.sub_chapter.sub_chapter_title
            
            # 디버깅 출력 (처음 3개만)
            if idx < 3:
                print(f"\n[결과 {idx+1}]")
                print(f"  - ID: {content.id}")
                print(f"  - 제목: {content.title}")
                print(f"  - 타입: {content.content_type.type_name if content.content_type else 'None'}")
                print(f"  - 대단원: {chapter_name}")
                print(f"  - 소단원: {subchapter_name}")
            
            results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name if content.content_type else '',
                'content_type_display': content.content_type.type_name if content.content_type else '',
                'chapter_name': chapter_name,
                'subchapter_name': subchapter_name,
                'preview': preview,
                'created_at': content.created_at.strftime('%Y-%m-%d') if content.created_at else '',
                'difficulty': content.meta_data.get('difficulty', '') if content.meta_data else '',
                'estimated_time': content.meta_data.get('estimated_time', 5) if content.meta_data else 5,
            })
        
        print(f"\n===== 콘텐츠 검색 완료 =====")
        print(f"최종 반환 결과: {len(results)}개")
        print(f"=============================\n")
        
        # step_counts를 response에 포함
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results),
            'step_counts': step_counts  # 단계별 카운트 추가
        })
        
    except Exception as e:
        import traceback
        print(f"\n!!!!! 에러 발생 !!!!!")
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        print(traceback.format_exc())
        print(f"!!!!!!!!!!!!!!!!!!!!!\n")
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


### 하나의 컨텐츠를 검색하여 요청

# contents_views.py에 추가

@login_required
@teacher_required
def api_content_detail(request, content_id):
    """단일 콘텐츠 상세 정보 API"""
    print(f"\n[api_content_detail] 시작 - content_id: {content_id}")
    print(f"[api_content_detail] 요청 사용자: {request.user.username}")
    
    try:
        content = get_object_or_404(Contents, id=content_id)
        print(f"[api_content_detail] 콘텐츠 찾음: {content.title}")
        
        # 권한 체크 - 본인 콘텐츠 또는 공개 콘텐츠만
        if content.created_by != request.user and not content.is_public:
            print(f"[api_content_detail] 권한 없음 - created_by: {content.created_by}, user: {request.user}")
            return JsonResponse({
                'success': False,
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        print(f"[api_content_detail] 권한 확인 완료")
        
        data = {
            'success': True,
            'content': {
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name,
                'created_at': content.created_at.strftime('%Y.%m.%d'),
                'preview': content.get_preview(50),
                'page': content.page,
                'answer': content.answer,
                'tags': content.tags,
                'meta_data': content.meta_data
            }
        }
        
        print(f"[api_content_detail] 응답 데이터 준비 완료")
        print(f"[api_content_detail] 반환할 콘텐츠: ID={content.id}, Title={content.title}")
        
        return JsonResponse(data)
        
    except Exception as e:
        print(f"[api_content_detail] 에러 발생: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



@login_required
@teacher_required
def api_contents_search_062118(request):
    """콘텐츠 검색 API"""
    try:
        teacher = request.user.teacher
        
        # 검색 파라미터 가져오기
        query = request.GET.get('q', '').strip()
        content_type_id = request.GET.get('content_type', '')
        chapter_search = request.GET.get('chapter', '').strip()  # ID 대신 제목 검색어
        course_id = request.GET.get('course_id', '')
        chasi_id = request.GET.get('chasi_id', '')  # 차시 ID 추가
        
        print(f"\n===== 콘텐츠 검색 시작 =====")
        print(f"요청 사용자: {request.user.username} (ID: {request.user.id})")
        print(f"검색 파라미터:")
        print(f"  - query: '{query}'")
        print(f"  - content_type_id: '{content_type_id}'")
        print(f"  - chapter_search: '{chapter_search}'")
        print(f"  - course_id: '{course_id}'")
        print(f"===========================")
        # 단계별 카운트 저장
        step_counts = {}
        
        # 기본 쿼리셋 (활성화된 콘텐츠만)
        contents = Contents.objects.filter(is_active=True)
        step_counts['step1'] = contents.count()
       
        
        
        # 현재 교사가 생성한 콘텐츠 또는 공개 콘텐츠
        contents = contents.filter(
            Q(created_by=request.user) | Q(is_public=True)
        )
        step_counts['step2'] = contents.count()
        
        # 차시 필터 (최우선 적용)
        if chasi_id:
            contents = contents.filter(
                chasislide__chasi_id=chasi_id
            ).distinct()
            step_counts['step_chasi'] = contents.count()

        print()
        
        # 텍스트 검색
        if query:
            contents = contents.filter(
                Q(title__icontains=query) |
                Q(page__icontains=query)
            )
            step_counts['step3'] = contents.count()
        
        # 콘텐츠 타입 필터
        if content_type_id:
            contents = contents.filter(content_type_id=content_type_id)
            step_counts['step4'] = contents.count()
        
        # 코스 필터링
        if course_id and not chasi_id:
            contents = contents.filter(
                chasislide__chasi__subject_id=course_id
            ).distinct()
            step_counts['step5'] = contents.count()
        
        # 대단원 제목으로 필터링
        if chapter_search and not chasi_id:
            contents = contents.filter(
                chasislide__chasi__chapter__chapter_title__icontains=chapter_search
            ).distinct()
            step_counts['step6'] = contents.count()
        
        # 정렬 및 제한
        contents = contents.select_related(
            'content_type', 'created_by'
        ).order_by('-created_at')[:50]
        
        # 결과 직렬화
        results = []
        for idx, content in enumerate(contents):
            # 미리보기 텍스트 생성
            preview = content.get_preview() if hasattr(content, 'get_preview') else ''
            
            # 이 콘텐츠가 사용된 첫 번째 슬라이드를 통해 대단원/소단원 정보 가져오기
            first_slide = content.chasislide_set.select_related(
                'chasi__chapter', 'chasi__sub_chapter'
            ).first()
            
            chapter_name = ''
            subchapter_name = ''
            if first_slide:
                if first_slide.chasi.chapter:
                    chapter_name = first_slide.chasi.chapter.chapter_title
                if first_slide.chasi.sub_chapter:
                    subchapter_name = first_slide.chasi.sub_chapter.sub_chapter_title
            
            # 디버깅 출력 (처음 3개만)
            if idx < 3:
                print(f"\n[결과 {idx+1}]")
                print(f"  - ID: {content.id}")
                print(f"  - 제목: {content.title}")
                print(f"  - 타입: {content.content_type.type_name if content.content_type else 'None'}")
                print(f"  - 대단원: {chapter_name}")
                print(f"  - 소단원: {subchapter_name}")
            
            results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name if content.content_type else '',
                'content_type_display': content.content_type.type_name if content.content_type else '',
                'chapter_name': chapter_name,
                'subchapter_name': subchapter_name,
                'preview': preview,
                'created_at': content.created_at.strftime('%Y-%m-%d') if content.created_at else '',
                'difficulty': content.meta_data.get('difficulty', '') if content.meta_data else '',
                'estimated_time': content.meta_data.get('estimated_time', 5) if content.meta_data else 5,
            })
        
        print(f"\n===== 콘텐츠 검색 완료 =====")
        print(f"최종 반환 결과: {len(results)}개")
        print(f"=============================\n")
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        import traceback
        print(f"\n!!!!! 에러 발생 !!!!!")
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        print(traceback.format_exc())
        print(f"!!!!!!!!!!!!!!!!!!!!!\n")
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


@login_required
@teacher_required
def api_contents_search_by_id(request):
    """콘텐츠 검색 API"""
    try:
        teacher = request.user.teacher
        
        # 검색 파라미터 가져오기
        query = request.GET.get('q', '').strip()
        content_type_id = request.GET.get('content_type', '')
        chapter_id = request.GET.get('chapter', '')
        subchapter_id = request.GET.get('subchapter', '')
        course_id = request.GET.get('course_id', '')
        
        print(f"\n===== 콘텐츠 검색 시작 =====")
        print(f"요청 사용자: {request.user.username} (ID: {request.user.id})")
        print(f"검색 파라미터:")
        print(f"  - query: '{query}'")
        print(f"  - content_type_id: '{content_type_id}'")
        print(f"  - chapter_id: '{chapter_id}'")
        print(f"  - subchapter_id: '{subchapter_id}'")
        print(f"  - course_id: '{course_id}'")
        print(f"===========================")
        
        # 기본 쿼리셋 (활성화된 콘텐츠만)
        contents = Contents.objects.filter(is_active=True)
        print(f"\n[1단계] 활성화된 콘텐츠: {contents.count()}개")
        
        # 현재 교사가 생성한 콘텐츠 또는 공개 콘텐츠
        contents = contents.filter(
            Q(created_by=request.user) | Q(is_public=True)
        )
        print(f"[2단계] 권한 필터 후 (created_by={request.user.id} OR is_public=True): {contents.count()}개")
        
        # 텍스트 검색
        if query:
            before_count = contents.count()
            contents = contents.filter(
                Q(title__icontains=query) |
                Q(page__icontains=query)
            )
            print(f"[3단계] 텍스트 검색 '{query}' 적용: {before_count}개 → {contents.count()}개")
        else:
            print(f"[3단계] 텍스트 검색 없음")
        
        # 콘텐츠 타입 필터
        if content_type_id:
            before_count = contents.count()
            contents = contents.filter(content_type_id=content_type_id)
            print(f"[4단계] 콘텐츠 타입 필터 (type_id={content_type_id}) 적용: {before_count}개 → {contents.count()}개")
        else:
            print(f"[4단계] 콘텐츠 타입 필터 없음")
        
        # 코스 필터링 (ChasiSlide를 통해 간접적으로)
        if course_id:
            before_count = contents.count()
            contents = contents.filter(
                chasislide__chasi__subject_id=course_id
            ).distinct()
            print(f"[5단계] 코스 필터 (course_id={course_id}) 적용: {before_count}개 → {contents.count()}개")
        else:
            print(f"[5단계] 코스 필터 없음")
        
        # 대단원 필터링
        if chapter_id:
            before_count = contents.count()
            contents = contents.filter(
                chasislide__chasi__chapter_id=chapter_id
            ).distinct()
            print(f"[6단계] 대단원 필터 (chapter_id={chapter_id}) 적용: {before_count}개 → {contents.count()}개")
        else:
            print(f"[6단계] 대단원 필터 없음")
        
        # 소단원 필터링
        if subchapter_id:
            before_count = contents.count()
            contents = contents.filter(
                chasislide__chasi__sub_chapter_id=subchapter_id
            ).distinct()
            print(f"[7단계] 소단원 필터 (subchapter_id={subchapter_id}) 적용: {before_count}개 → {contents.count()}개")
        else:
            print(f"[7단계] 소단원 필터 없음")
        
        # 정렬 및 제한
        total_before_limit = contents.count()
        contents = contents.select_related(
            'content_type', 'created_by'
        ).order_by('-created_at')[:50]  # 최대 50개
        
        print(f"\n[최종] 정렬 및 제한 적용")
        print(f"  - 제한 전: {total_before_limit}개")
        print(f"  - 제한 후: {len(contents)}개 (최대 50개)")
        
        # SQL 쿼리 확인 (디버깅용)
        print(f"\n[SQL 쿼리]")
        print(str(contents.query))
        
        # 결과 직렬화
        results = []
        for idx, content in enumerate(contents):
            # 미리보기 텍스트 생성
            preview = content.get_preview() if hasattr(content, 'get_preview') else ''
            
            # 이 콘텐츠가 사용된 첫 번째 슬라이드를 통해 대단원/소단원 정보 가져오기
            first_slide = content.chasislide_set.select_related(
                'chasi__chapter', 'chasi__sub_chapter'
            ).first()
            
            chapter_name = ''
            subchapter_name = ''
            if first_slide:
                chapter_name = first_slide.chasi.chapter.chapter_title
                subchapter_name = first_slide.chasi.sub_chapter.sub_chapter_title
            
            if idx < 3:  # 처음 3개 결과만 상세 출력
                print(f"\n[결과 {idx+1}]")
                print(f"  - ID: {content.id}")
                print(f"  - 제목: {content.title}")
                print(f"  - 타입: {content.content_type.type_name if content.content_type else 'None'}")
                print(f"  - 생성자: {content.created_by.username if content.created_by else 'None'}")
                print(f"  - 공개여부: {content.is_public}")
                print(f"  - 대단원: {chapter_name}")
                print(f"  - 소단원: {subchapter_name}")
            
            results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name if content.content_type else '',
                'content_type_display': content.content_type.type_name if content.content_type else '',
                'chapter_name': chapter_name,
                'subchapter_name': subchapter_name,
                'preview': preview,
                'created_at': content.created_at.strftime('%Y-%m-%d') if content.created_at else '',
                'difficulty': content.meta_data.get('difficulty', '') if content.meta_data else '',
                'estimated_time': content.meta_data.get('estimated_time', 5) if content.meta_data else 5,
            })
        
        print(f"\n===== 콘텐츠 검색 완료 =====")
        print(f"최종 반환 결과: {len(results)}개")
        print(f"=============================\n")
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        import traceback
        print(f"\n!!!!! 에러 발생 !!!!!")
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        print(traceback.format_exc())
        print(f"!!!!!!!!!!!!!!!!!!!!!\n")
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


@login_required
@teacher_required
def api_contents_search_0622(request):
    """콘텐츠 검색 API"""
    try:
        teacher = request.user.teacher
        
        # 검색 파라미터 가져오기
        query = request.GET.get('q', '').strip()
        content_type_id = request.GET.get('content_type', '')
        chapter_id = request.GET.get('chapter', '')
        subchapter_id = request.GET.get('subchapter', '')
        course_id = request.GET.get('course_id', '')
        
        # 기본 쿼리셋 (활성화된 콘텐츠만)
        contents = Contents.objects.filter(is_active=True)
        
        # 교사의 콘텐츠만 (혹은 공개 콘텐츠)
        contents = contents.filter(
            Q(teacher=teacher) | Q(is_public=True)
        )
        
        # 텍스트 검색
        if query:
            contents = contents.filter(
                Q(title__icontains=query) |
                Q(page__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # 콘텐츠 타입 필터
        if content_type_id:
            contents = contents.filter(content_type_id=content_type_id)
        
        # 대단원 필터
        if chapter_id:
            contents = contents.filter(chapter_id=chapter_id)
        
        # 소단원 필터
        if subchapter_id:
            contents = contents.filter(subchapter_id=subchapter_id)
        
        # 코스 필터 (대단원을 통해)
        if course_id:
            contents = contents.filter(chapter__subject_id=course_id)
        
        # 정렬 및 제한
        contents = contents.select_related(
            'content_type', 'chapter', 'subchapter'
        ).order_by('-created_at')[:50]  # 최대 50개
        
        # 결과 직렬화
        results = []
        for content in contents:
            # 미리보기 텍스트 생성
            preview = ''
            if content.page:
                # HTML 태그 제거하고 첫 100자만
                import re
                preview = re.sub(r'<[^>]+>', '', content.page)[:100]
            
            results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name if content.content_type else '',
                'content_type_display': content.content_type.type_name if content.content_type else '',
                'chapter_name': content.chapter.chapter_title if content.chapter else '',
                'subchapter_name': content.subchapter.sub_chapter_title if content.subchapter else '',
                'preview': preview,
                'created_at': content.created_at.strftime('%Y-%m-%d') if content.created_at else '',
                'difficulty': getattr(content, 'difficulty', ''),
                'estimated_time': getattr(content, 'estimated_time', 5),
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


@login_required
@teacher_required
def api_content_types_by_category(request, category):
    """카테고리별 콘텐츠 타입 목록 API"""
    try:
        content_types = ContentType.objects.filter(
            category_name__category_name=category,
            is_active=True
        )
        
        
        data = {
            'success': True,
            'content_types': [
                {'id': ct.id, 'type_name': ct.type_name}
                for ct in content_types
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)