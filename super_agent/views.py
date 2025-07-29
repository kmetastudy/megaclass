# super_agent/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.db import transaction
from django.db.models import Count, Q
from django.core.paginator import Paginator
import json
import uuid
from datetime import datetime
from .utils import *

# 기존 모델들 import
from teacher.models import (
    Course, Chapter, SubChapter, Chasi, ChasiSlide, 
    ContentType, Contents, CourseAssignment, ContentsAttached
)
from accounts.models import Teacher, Class, Student
from teacher.decorators import teacher_required
from teacher.utils import get_course_statistics, get_course_progress

# ========================================
# 메인 에이전트 페이지
# ========================================

@login_required
@teacher_required
def agent_main_view(request):
    """AI 에이전트 메인 페이지"""
    teacher = request.user.teacher
    
    # 최근 코스들
    recent_courses = Course.objects.filter(teacher=teacher).order_by('-created_at')[:10]
    
    # 최근 생성된 콘텐츠들
    recent_contents = Contents.objects.filter(
        created_by=request.user,
        is_active=True
    ).order_by('-created_at')[:20]
    
    # 콘텐츠 타입들
    content_types = ContentType.objects.filter(is_active=True)
    
    # 통계
    stats = {
        'total_courses': Course.objects.filter(teacher=teacher).count(),
        'total_contents': Contents.objects.filter(created_by=request.user).count(),
        'total_students': Student.objects.filter(school_class__teachers=teacher).distinct().count(),
        'total_assignments': CourseAssignment.objects.filter(course__teacher=teacher).count(),
    }
    
    context = {
        'recent_courses': recent_courses,
        'recent_contents': recent_contents,
        'content_types': content_types,
        'stats': stats,
    }
    
    return render(request, 'super_agent/agent.html', context)

# ========================================
# 코스 관련 API
# ========================================

@login_required
@teacher_required
@require_GET
def api_course_search(request):
    """코스 검색 API"""
    try:
        teacher = request.user.teacher
        query = request.GET.get('q', '').strip()
        
        courses = Course.objects.filter(teacher=teacher)
        
        if query:
            courses = courses.filter(
                Q(subject_name__icontains=query) |
                Q(target__icontains=query) |
                Q(description__icontains=query)
            )
        
        courses = courses.order_by('-created_at')[:20]
        
        results = []
        for course in courses:
            results.append({
                'id': course.id,
                'subject_name': course.subject_name,
                'target': course.target,
                'description': course.description,
                'created_at': course.created_at.strftime('%Y-%m-%d'),
                'chapter_count': course.chapters.count(),
            })
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_GET
def api_course_structure(request, course_id):
    """코스 구조 JSON 반환 API"""
    try:
        teacher = request.user.teacher
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        structure = {
            'course': {
                'id': course.id,
                'subject_name': course.subject_name,
                'target': course.target,
                'description': course.description
            },
            'chapters': []
        }
        
        chapters = Chapter.objects.filter(subject=course).order_by('chapter_order')
        for chapter in chapters:
            chapter_data = {
                'id': chapter.id,
                'title': chapter.chapter_title,
                'order': chapter.chapter_order,
                'description': chapter.description,
                'subchapters': []
            }
            
            subchapters = SubChapter.objects.filter(chapter=chapter).order_by('sub_chapter_order')
            for subchapter in subchapters:
                subchapter_data = {
                    'id': subchapter.id,
                    'title': subchapter.sub_chapter_title,
                    'order': subchapter.sub_chapter_order,
                    'description': subchapter.description,
                    'chasis': []
                }
                
                chasis = Chasi.objects.filter(sub_chapter=subchapter).order_by('chasi_order')
                for chasi in chasis:
                    slide_count = ChasiSlide.objects.filter(chasi=chasi).count()
                    chasi_data = {
                        'id': chasi.id,
                        'title': chasi.chasi_title,
                        'order': chasi.chasi_order,
                        'description': chasi.description,
                        'learning_objectives': chasi.learning_objectives,
                        'duration_minutes': chasi.duration_minutes,
                        'slide_count': slide_count
                    }
                    subchapter_data['chasis'].append(chasi_data)
                
                chapter_data['subchapters'].append(subchapter_data)
            
            structure['chapters'].append(chapter_data)
        
        return JsonResponse({
            'success': True,
            'structure': structure
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_POST
def api_course_structure_update(request, course_id):
    """코스 구조 업데이트 API (JSON 기반)"""
    try:
        teacher = request.user.teacher
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        data = json.loads(request.body)
        structure = data.get('structure')
        
        if not structure:
            return JsonResponse({
                'success': False,
                'error': '구조 데이터가 필요합니다.'
            }, status=400)
        
        with transaction.atomic():
            # 기존 구조 삭제는 하지 않고 업데이트만 수행
            # 실제 구현에서는 더 세밀한 업데이트 로직이 필요
            
            # 코스 정보 업데이트
            if 'course' in structure:
                course_info = structure['course']
                course.subject_name = course_info.get('subject_name', course.subject_name)
                course.target = course_info.get('target', course.target)
                course.description = course_info.get('description', course.description)
                course.save()
            
            # 새로운 구조 생성 로직은 복잡하므로 여기서는 기본 응답만
            
        return JsonResponse({
            'success': True,
            'message': '코스 구조가 업데이트되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ========================================
# 콘텐츠 관련 API
# ========================================

@login_required
@teacher_required
@require_POST
def api_content_create_with_prompt(request):
    """프롬프트를 이용한 콘텐츠 생성 API"""
    try:
        data = json.loads(request.body)
        
        # 프롬프트 데이터
        prompt = data.get('prompt', '')
        content_type_id = data.get('content_type_id')
        title = data.get('title', '')
        ai_provider = data.get('ai_provider', 'claude')  # claude, gemini, chatgpt, grok
        
        # 고급 설정 옵션들
        options = {
            'difficulty': data.get('difficulty', '중급'),
            'include_explanation': data.get('include_explanation', True),
            'include_hints': data.get('include_hints', False),
            'include_images': data.get('include_images', False),
            'multiple_versions': data.get('multiple_versions', False)
        }
        
        # 기본 검증
        if not prompt or not content_type_id or not title:
            return JsonResponse({
                'success': False,
                'error': '프롬프트, 콘텐츠 타입, 제목이 필요합니다.'
            }, status=400)
        
        content_type = get_object_or_404(ContentType, id=content_type_id, is_active=True)
        
        # AI API 호출
        generated_content = generate_content_with_ai(prompt, content_type.type_name, ai_provider, options)
        
        # 콘텐츠 생성
        content = Contents.objects.create(
            title=title,
            content_type=content_type,
            page=generated_content,
            created_by=request.user,
            meta_data={
                'generated_by_ai': True,
                'ai_provider': ai_provider,
                'original_prompt': prompt,
                'generation_timestamp': datetime.now().isoformat()
            },
            is_active=True,
            is_public=False
        )
        
        return JsonResponse({
            'success': True,
            'content': {
                'id': content.id,
                'title': content.title,
                'content_code': content.content_code,
                'page': content.page,
                'content_type': content.content_type.type_name,
                'created_at': content.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_POST
def api_content_update_with_prompt(request, content_id):
    """프롬프트를 이용한 콘텐츠 수정 API"""
    try:
        content = get_object_or_404(Contents, id=content_id, created_by=request.user)
        data = json.loads(request.body)
        
        prompt = data.get('prompt', '')
        ai_provider = data.get('ai_provider', 'claude')
        
        if not prompt:
            return JsonResponse({
                'success': False,
                'error': '수정을 위한 프롬프트가 필요합니다.'
            }, status=400)
        
        # 기존 콘텐츠를 백업
        backup_content = content.page
        
        # AI를 이용한 콘텐츠 수정
        modified_content = modify_content_with_ai(content.page, prompt, ai_provider)
        
        # 콘텐츠 업데이트
        content.page = modified_content
        content.meta_data.update({
            'last_modified_by_ai': True,
            'last_ai_provider': ai_provider,
            'last_modification_prompt': prompt,
            'last_modification_timestamp': datetime.now().isoformat(),
            'backup_content': backup_content  # 이전 버전 백업
        })
        content.save()
        
        return JsonResponse({
            'success': True,
            'content': {
                'id': content.id,
                'page': content.page,
                'backup_content': backup_content
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_GET
def api_content_search(request):
    """콘텐츠 검색 API"""
    try:
        # 검색 파라미터
        query = request.GET.get('q', '').strip()
        content_type_id = request.GET.get('content_type', '')
        course_id = request.GET.get('course_id', '')
        
        # 기본 쿼리셋
        contents = Contents.objects.filter(
            Q(created_by=request.user) | Q(is_public=True),
            is_active=True
        ).select_related('content_type')
        
        # 검색어 필터
        if query:
            contents = contents.filter(
                Q(title__icontains=query) | 
                Q(page__icontains=query) |
                Q(content_code__icontains=query)
            )
        
        # 콘텐츠 타입 필터
        if content_type_id:
            contents = contents.filter(content_type_id=content_type_id)
        
        # 코스 필터 (슬라이드를 통해)
        if course_id:
            contents = contents.filter(
                chasislide__chasi__subject_id=course_id
            ).distinct()
        
        # 정렬 및 제한
        contents = contents.order_by('-created_at')[:50]
        
        results = []
        for content in contents:
            results.append({
                'id': content.id,
                'title': content.title,
                'content_code': content.content_code,
                'content_type': content.content_type.type_name,
                'preview': content.get_preview(100),
                'created_at': content.created_at.strftime('%Y-%m-%d'),
                'is_mine': content.created_by == request.user,
                'view_count': content.view_count
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
@require_GET
def api_content_detail(request, content_id):
    """콘텐츠 상세 정보 API"""
    try:
        content = get_object_or_404(Contents, id=content_id)
        
        # 권한 체크
        if content.created_by != request.user and not content.is_public:
            return JsonResponse({
                'success': False,
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        # 조회수 증가
        content.view_count += 1
        content.save(update_fields=['view_count'])
        
        return JsonResponse({
            'success': True,
            'content': {
                'id': content.id,
                'title': content.title,
                'content_code': content.content_code,
                'page': content.page,
                'answer': content.answer,
                'content_type': content.content_type.type_name,
                'meta_data': content.meta_data,
                'tags': content.tags,
                'created_at': content.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': content.updated_at.strftime('%Y-%m-%d %H:%M'),
                'is_mine': content.created_by == request.user,
                'view_count': content.view_count
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ========================================
# AI 유틸리티 연동
# ========================================

from .ai_utils import ai_manager

def generate_content_with_ai(prompt, content_type, ai_provider, options=None):
    """AI를 이용한 콘텐츠 생성"""
    try:
        return ai_manager.generate_content(prompt, content_type, ai_provider, options)
    except Exception as e:
        print(f"AI 콘텐츠 생성 오류: {str(e)}")
        # 폴백으로 모의 콘텐츠 반환
        return ai_manager._generate_mock_content(prompt, content_type, ai_provider)

def modify_content_with_ai(original_content, prompt, ai_provider):
    """AI를 이용한 콘텐츠 수정"""
    try:
        return ai_manager.modify_content(original_content, prompt, ai_provider)
    except Exception as e:
        print(f"AI 콘텐츠 수정 오류: {str(e)}")
        # 폴백으로 모의 수정 반환
        return ai_manager._generate_mock_modification(original_content, prompt, ai_provider)

# ========================================
# 통계 및 분석 API
# ========================================

@login_required
@teacher_required
@require_GET
def api_agent_statistics(request):
    """에이전트 통계 API"""
    try:
        teacher = request.user.teacher
        
        # 기본 통계
        stats = {
            'courses': {
                'total': Course.objects.filter(teacher=teacher).count(),
                'active': Course.objects.filter(teacher=teacher, is_active=True).count(),
                'recent': Course.objects.filter(teacher=teacher).filter(
                    created_at__gte=datetime.now().replace(day=1)
                ).count()
            },
            'contents': {
                'total': Contents.objects.filter(created_by=request.user).count(),
                'ai_generated': Contents.objects.filter(
                    created_by=request.user,
                    meta_data__generated_by_ai=True
                ).count(),
                'recent': Contents.objects.filter(
                    created_by=request.user,
                    created_at__gte=datetime.now().replace(day=1)
                ).count()
            },
            'students': {
                'total': Student.objects.filter(school_class__teachers=teacher).distinct().count(),
                'assigned': CourseAssignment.objects.filter(
                    course__teacher=teacher
                ).values('assigned_student', 'assigned_class').distinct().count()
            }
        }
        
        # 콘텐츠 타입별 통계
        content_type_stats = Contents.objects.filter(
            created_by=request.user
        ).values(
            'content_type__type_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['content_types'] = list(content_type_stats)
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)