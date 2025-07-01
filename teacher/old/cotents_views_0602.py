# teacher/views/contents_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
import json

from ..models import Contents, ContentType
from ..forms import ContentsForm

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
    queryset = queryset.select_related('content_type')
    
    # 페이지네이션
    paginator = Paginator(queryset, 20)  # 페이지당 20개
    page = request.GET.get('page')
    
    try:
        contents = paginator.page(page)
    except PageNotAnInteger:
        # 페이지 번호가 정수가 아닌 경우 첫 페이지 표시
        contents = paginator.page(1)
    except EmptyPage:
        # 페이지가 범위를 벗어난 경우 마지막 페이지 표시
        contents = paginator.page(paginator.num_pages)
    
    # 페이지 번호 범위 계산 (현재 페이지 주변 5개씩 표시)
    current_page = contents.number
    start_page = max(1, current_page - 5)
    end_page = min(paginator.num_pages, current_page + 5)
    page_range = range(start_page, end_page + 1)
    
    context = {
        'contents': contents,
        'content_types': ContentType.objects.filter(is_active=True),
        'selected_type': content_type,
        'search_query': search or '',
        'page_obj': contents,  # 템플릿 호환성
        'is_paginated': paginator.num_pages > 1,
        'page_range': page_range,
    }
    
    return render(request, 'teacher/contents/list.html', context)

@login_required
def contents_create(request):
    """콘텐츠 생성"""
    if request.method == 'POST':
        form = ContentsForm(request.POST)
        if form.is_valid():
            content = form.save(commit=False)
            content.created_by = request.user
            
            # JSON 필드 유효성 검사
            try:
                if form.cleaned_data.get('meta_data'):
                    json.loads(form.cleaned_data['meta_data'])
                if form.cleaned_data.get('tags'):
                    json.loads(form.cleaned_data['tags'])
            except json.JSONDecodeError as e:
                form.add_error(None, f'JSON 형식 오류: {str(e)}')
                return render(request, 'teacher/contents/create.html', {'form': form})
            
            content.save()
            messages.success(request, '콘텐츠가 생성되었습니다.')
            
            # AJAX 요청인 경우 JSON 응답
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'content_id': content.id,
                    'message': '콘텐츠가 생성되었습니다.',
                    'redirect_url': reverse('teacher:contents_list')
                })
            
            return redirect('teacher:contents_list')
    else:
        form = ContentsForm()
    
    context = {
        'form': form,
        'content_types': ContentType.objects.filter(is_active=True),
    }
    
    return render(request, 'teacher/contents/create.html', context)

@login_required
def contents_edit(request, content_id):
    """콘텐츠 수정"""
    # 본인이 생성한 콘텐츠만 수정 가능
    content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ContentsForm(request.POST, instance=content)
        if form.is_valid():
            # JSON 필드 유효성 검사
            try:
                if form.cleaned_data.get('meta_data'):
                    json.loads(form.cleaned_data['meta_data'])
                if form.cleaned_data.get('tags'):
                    json.loads(form.cleaned_data['tags'])
            except json.JSONDecodeError as e:
                form.add_error(None, f'JSON 형식 오류: {str(e)}')
                return render(request, 'teacher/contents/edit.html', {
                    'form': form,
                    'object': content
                })
            
            form.save()
            messages.success(request, '콘텐츠가 수정되었습니다.')
            
            # AJAX 요청인 경우 JSON 응답
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '콘텐츠가 수정되었습니다.',
                    'redirect_url': reverse('teacher:contents_list')
                })
            
            return redirect('teacher:contents_list')
    else:
        form = ContentsForm(instance=content)
    
    context = {
        'form': form,
        'object': content,  # 템플릿 호환성
        'content': content,
        'content_types': ContentType.objects.filter(is_active=True),
    }
    
    return render(request, 'teacher/contents/edit.html', context)

@login_required
@require_POST
def contents_delete(request, content_id):
    """콘텐츠 삭제"""
    # 본인이 생성한 콘텐츠만 삭제 가능
    content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    # 이 콘텐츠를 사용하는 슬라이드가 있는지 확인
    slide_count = content.chasislide_set.count()
    if slide_count > 0:
        messages.error(
            request, 
            f'이 콘텐츠는 {slide_count}개의 슬라이드에서 사용 중이므로 삭제할 수 없습니다.'
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': f'이 콘텐츠는 {slide_count}개의 슬라이드에서 사용 중입니다.'
            }, status=400)
        
        return redirect('teacher:contents_list')
    
    # 콘텐츠 삭제
    content_title = content.title
    content.delete()
    messages.success(request, f'"{content_title}" 콘텐츠가 삭제되었습니다.')
    
    # AJAX 요청인 경우 JSON 응답
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'"{content_title}" 콘텐츠가 삭제되었습니다.'
        })
    
    return redirect('teacher:contents_list')

# 추가 유틸리티 함수들

@login_required
def contents_preview(request, content_id):
    """콘텐츠 미리보기"""
    content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    context = {
        'content': content,
        'is_preview': True,
    }
    
    # AJAX 요청인 경우 부분 템플릿 렌더링
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'teacher/contents/preview_partial.html', context)
    
    return render(request, 'teacher/contents/preview.html', context)

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
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'content_id': duplicated.id,
            'message': '콘텐츠가 복제되었습니다.'
        })
    
    return redirect('teacher:contents_edit', content_id=duplicated.id)

@login_required
def contents_toggle_active(request, content_id):
    """콘텐츠 활성화/비활성화 토글"""
    content = get_object_or_404(Contents, id=content_id, created_by=request.user)
    
    content.is_active = not content.is_active
    content.save(update_fields=['is_active'])
    
    status = "활성화" if content.is_active else "비활성화"
    messages.success(request, f'콘텐츠가 {status}되었습니다.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_active': content.is_active,
            'message': f'콘텐츠가 {status}되었습니다.'
        })
    
    return redirect('teacher:contents_list')

@login_required
def content_type_template(request, type_id):
    """콘텐츠 타입별 기본 템플릿 반환"""
    content_type = get_object_or_404(ContentType, id=type_id)
    
    templates = {
        '객관식 문제': '''<div class="question-container">
    <h3>문제</h3>
    <p>다음 중 올바른 것은?</p>
    <ol type="1">
        <li>첫 번째 보기</li>
        <li>두 번째 보기</li>
        <li>세 번째 보기</li>
        <li>네 번째 보기</li>
    </ol>
</div>''',
        '단답형 문제': '''<div class="question-container">
    <h3>문제</h3>
    <p>다음 빈칸에 알맞은 답을 쓰시오.</p>
    <p>____는 우리나라의 수도입니다.</p>
</div>''',
        '서술형 문제': '''<div class="question-container">
    <h3>문제</h3>
    <p>다음 주제에 대해 서술하시오.</p>
    <p>[서술 문제]</p>
</div>''',
        # ... 기타 템플릿
    }
    
    template = templates.get(content_type.type_name, '<div>콘텐츠를 입력하세요.</div>')
    
    return JsonResponse({
        'template': template,
        'type_name': content_type.type_name
    })

@login_required
def contents_search(request):
    """콘텐츠 검색 (자동완성용)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    contents = Contents.objects.filter(
        created_by=request.user,
        is_active=True,
        title__icontains=query
    ).select_related('content_type')[:10]
    
    results = [{
        'id': content.id,
        'title': content.title,
        'type': content.content_type.type_name,
        'preview': content.get_preview(50)
    } for content in contents]
    
    return JsonResponse({'results': results})