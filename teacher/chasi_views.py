# teacher/chasi_views.py
# 차시 관련 뷰와 API 엔드포인트

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.db import transaction
from django.db.models import Count, Q
from django.core.paginator import Paginator
import json

# 모델 import
from .models import (
    Course, Chapter, SubChapter, Chasi, ChasiSlide, 
    ContentType, Contents, CourseAssignment, ContentsAttached
)
from accounts.models import Teacher, Class, Student
from .decorators import teacher_required

# ========================================
# API 뷰들
# ========================================
@login_required
@teacher_required
@require_GET
def api_contents_list(request):
    """차시에서 사용할 수 있는 콘텐츠 목록 API"""
    try:
        chasi_id = request.GET.get('chasi_id')
        
        # ★★★ 수정: 교사 본인의 콘텐츠만 가져오도록 변경 ★★★
        contents = Contents.objects.filter(
            created_by=request.user,  # 교사 본인이 생성한 것만
            is_active=True
        ).select_related('content_type').order_by('-created_at')[:50]
        # 공개 콘텐츠(is_public=True)를 제외했습니다
        
        contents_data = []
        for content in contents:
            contents_data.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name,
                'created_at': content.created_at.strftime('%Y.%m.%d'),
                'preview': content.get_preview(50)
            })
        
        return JsonResponse({
            'success': True,
            'contents': contents_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@teacher_required
@require_GET
def api_contents_list_0621(request):
    """차시에서 사용할 수 있는 콘텐츠 목록 API"""
    try:
        chasi_id = request.GET.get('chasi_id')
        
        # 사용 가능한 콘텐츠 조회 (교사 본인 것만)
        contents = Contents.objects.filter(
            created_by=request.user,
            is_active=True
        ).select_related('content_type').order_by('-created_at')[:50]
        
        contents_data = []
        for content in contents:
            contents_data.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name,
                'created_at': content.created_at.strftime('%Y.%m.%d'),
                'preview': content.get_preview(50)
            })
        
        return JsonResponse({
            'success': True,
            'contents': contents_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_GET
def api_chasi_slides(request, chasi_id):
    """차시의 슬라이드 목록 API"""
    try:
        teacher = request.user.teacher
        chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
        
        slides = ChasiSlide.objects.filter(chasi=chasi).select_related(
            'content', 'content_type'
        ).order_by('slide_number')
        
        slides_data = []
        for slide in slides:
            slides_data.append({
                'id': slide.id,
                'slide_number': slide.slide_number,
                'slide_title': slide.slide_title or '',
                'content_id': slide.content.id,
                'content_title': slide.content.title,
                'content_type': slide.content_type.type_name,
                'estimated_time': slide.estimated_time,
                'instructor_notes': slide.instructor_notes or '',
                'is_active': slide.is_active
            })
        
        return JsonResponse({
            'success': True,
            'slides': slides_data,
            'total': len(slides_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_POST
def api_slide_add(request, chasi_id):
    """슬라이드 추가 API"""
    try:
        teacher = request.user.teacher
        chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
        
        # POST 데이터 파싱
        content_id = request.POST.get('content_id')
        slide_title = request.POST.get('slide_title', '')
        instructor_notes = request.POST.get('instructor_notes', '')
        estimated_time = int(request.POST.get('estimated_time', 5))
        
        if not content_id:
            return JsonResponse({
                'success': False,
                'error': '콘텐츠를 선택해주세요.'
            }, status=400)
        
        # 콘텐츠 확인
        # content = get_object_or_404(Contents, id=content_id, created_by=request.user)
        content = get_object_or_404(Contents, id=content_id)
        
        with transaction.atomic():
            # 슬라이드 번호 자동 계산
            last_slide = ChasiSlide.objects.filter(chasi=chasi).order_by('-slide_number').first()
            slide_number = (last_slide.slide_number + 1) if last_slide else 1
            
            # 슬라이드 생성
            slide = ChasiSlide.objects.create(
                chasi=chasi,
                slide_number=slide_number,
                slide_title=slide_title,
                content_type=content.content_type,
                content=content,
                instructor_notes=instructor_notes,
                estimated_time=estimated_time,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': '슬라이드가 추가되었습니다.',
                'slide': {
                    'id': slide.id,
                    'slide_number': slide.slide_number,
                    'content_title': content.title
                }
            })
            
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': '올바른 예상 시간을 입력해주세요.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_POST
def api_slide_delete(request, slide_id):
    """슬라이드 삭제 API"""
    try:
        teacher = request.user.teacher
        slide = get_object_or_404(ChasiSlide, id=slide_id, chasi__subject__teacher=teacher)
        chasi = slide.chasi
        
        with transaction.atomic():
            # 슬라이드 삭제
            slide_number = slide.slide_number
            slide.delete()
            
            # 남은 슬라이드 번호 재정렬
            remaining_slides = ChasiSlide.objects.filter(
                chasi=chasi,
                slide_number__gt=slide_number
            ).order_by('slide_number')
            
            for remaining_slide in remaining_slides:
                remaining_slide.slide_number -= 1
                remaining_slide.save(update_fields=['slide_number'])
        
        return JsonResponse({
            'success': True,
            'message': '슬라이드가 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@teacher_required
@require_POST
def api_slide_reorder(request, chasi_id):
    """슬라이드 순서 변경 API"""
    try:
        teacher = request.user.teacher
        chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
        
        data = json.loads(request.body)
        slide_orders = data.get('slide_orders', [])
        
        with transaction.atomic():
            for item in slide_orders:
                slide_id = item['slide_id']
                new_order = item['order']
                
                ChasiSlide.objects.filter(
                    id=slide_id, 
                    chasi=chasi
                ).update(slide_number=new_order)
        
        return JsonResponse({
            'success': True,
            'message': '슬라이드 순서가 변경되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ========================================
# 기존 페이지 뷰들
# ========================================

@login_required
@teacher_required
def chasi_slide_manage(request, chasi_id):
    """차시 슬라이드 관리 페이지"""
    chasi = get_object_or_404(
        Chasi.objects.select_related('sub_chapter__chapter__subject'),
        id=chasi_id,
    )
    
    # 권한 확인
    if chasi.sub_chapter.chapter.subject.teacher != request.user.teacher:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('teacher:dashboard')
    
    slides = ChasiSlide.objects.filter(chasi=chasi).select_related(
        'content_type', 'content'
    ).order_by('slide_number')
    
    content_types = ContentType.objects.filter(is_active=True)
    available_contents = Contents.objects.filter(
        created_by=request.user,
        is_active=True
    ).select_related('content_type').order_by('-created_at')[:20]
    
    context = {
        'chasi': chasi,
        'subchapter': chasi.sub_chapter,
        'chapter': chasi.sub_chapter.chapter,
        'course': chasi.sub_chapter.chapter.subject,
        'slides': slides,
        'content_types': content_types,
        'available_contents': available_contents,
    }
    
    return render(request, 'teacher/courses/chasis/slide_manage.html', context)

@login_required
@teacher_required
def chasi_slide_add(request, chasi_id):
    """차시 슬라이드 추가 페이지"""
    chasi = get_object_or_404(
        Chasi.objects.select_related('sub_chapter__chapter__subject__teacher'),
        id=chasi_id
    )
    
    if chasi.sub_chapter.chapter.subject.teacher.user != request.user:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('teacher:dashboard')
    
    if request.method == 'POST':
        content_id = request.POST.get('content_id')
        if not content_id:
            messages.error(request, '콘텐츠를 선택해주세요.')
            return redirect('teacher:chasi_slide_add', chasi_id=chasi_id)
        
        try:
            content = Contents.objects.get(id=content_id, created_by=request.user)
            
            last_slide = ChasiSlide.objects.filter(chasi=chasi).order_by('-slide_number').first()
            slide_number = (last_slide.slide_number + 1) if last_slide else 1
            
            slide = ChasiSlide.objects.create(
                chasi=chasi,
                slide_number=slide_number,
                content_type=content.content_type,
                content=content,
                slide_title=request.POST.get('slide_title', ''),
                instructor_notes=request.POST.get('instructor_notes', ''),
                estimated_time=int(request.POST.get('estimated_time', 5))
            )
            
            messages.success(request, '슬라이드가 추가되었습니다.')
            return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)
            
        except Contents.DoesNotExist:
            messages.error(request, '선택한 콘텐츠를 찾을 수 없습니다.')
        except ValueError:
            messages.error(request, '올바른 예상 시간을 입력해주세요.')
        except Exception as e:
            messages.error(request, f'슬라이드 추가 중 오류가 발생했습니다: {str(e)}')
    
    content_types = ContentType.objects.filter(is_active=True)
    available_contents = Contents.objects.filter(
        created_by=request.user,
        is_active=True
    ).select_related('content_type').order_by('-created_at')
    
    context = {
        'chasi': chasi,
        'course': chasi.sub_chapter.chapter.subject,
        'chapter': chasi.sub_chapter.chapter,
        'subchapter': chasi.sub_chapter,
        'content_types': content_types,
        'available_contents': available_contents,
    }
    
    return render(request, 'teacher/courses/chasis/slide_add.html', context)

@login_required
@teacher_required
def chasi_slide_edit(request, slide_id):
    """슬라이드 수정"""
    teacher = request.user.teacher
    slide = get_object_or_404(ChasiSlide, id=slide_id, chasi__subject__teacher=teacher)
    
    if request.method == 'POST':
        # 수정 로직 구현
        slide.slide_title = request.POST.get('slide_title', '')
        slide.instructor_notes = request.POST.get('instructor_notes', '')
        slide.estimated_time = int(request.POST.get('estimated_time', 5))
        
        # 콘텐츠 변경
        content_id = request.POST.get('content_id')
        if content_id:
            content = get_object_or_404(Contents, id=content_id, created_by=request.user)
            slide.content = content
            slide.content_type = content.content_type
        
        slide.save()
        messages.success(request, '슬라이드가 수정되었습니다.')
        return redirect('teacher:chasi_slide_manage', chasi_id=slide.chasi.id)
    
    context = {
        'slide': slide,
        'chasi': slide.chasi,
        'available_contents': Contents.objects.filter(
            created_by=request.user,
            is_active=True
        ).select_related('content_type').order_by('-created_at')
    }
    return render(request, 'teacher/courses/chasis/slide_edit.html', context)

@login_required
@teacher_required
def chasi_slide_delete(request, slide_id):
    """슬라이드 삭제 (AJAX 지원)"""
    teacher = request.user.teacher
    slide = get_object_or_404(ChasiSlide, id=slide_id, chasi__subject__teacher=teacher)
    chasi = slide.chasi
    
    if request.method == 'POST':
        with transaction.atomic():
            slide_number = slide.slide_number
            slide.delete()
            
            # 슬라이드 번호 재정렬
            remaining_slides = ChasiSlide.objects.filter(
                chasi=chasi,
                slide_number__gt=slide_number
            ).order_by('slide_number')
            
            for remaining_slide in remaining_slides:
                remaining_slide.slide_number -= 1
                remaining_slide.save(update_fields=['slide_number'])
        
        # AJAX 요청인 경우
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '슬라이드가 삭제되었습니다.'
            })
        
        messages.success(request, '슬라이드가 삭제되었습니다.')
        return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)
    
    context = {
        'slide': slide,
        'chasi': chasi,
    }
    return render(request, 'teacher/courses/chasis/slide_delete.html', context)

@login_required
@teacher_required
def chasi_preview(request, chasi_id):
    """차시 미리보기"""
    teacher = request.user.teacher
    chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
    
    slides = chasi.teacher_slides.select_related('content', 'content_type').order_by('slide_number')
    
    context = {
        'chasi': chasi,
        'slides': slides,
        'total_slides': slides.count(),
        'total_time': sum(slide.estimated_time for slide in slides),
    }
    
    return render(request, 'teacher/courses/chasis/preview.html', context)

# 별칭 함수 (기존 코드와의 호환성을 위해)
def reorder_slides(request, chasi_id):
    """슬라이드 순서 변경 (api_slide_reorder로 리다이렉트)"""
    return api_slide_reorder(request, chasi_id)


# teacher/chasi_views.py에 추가

@login_required
@teacher_required
@require_POST
def api_contents_list_with_selected(request):
    """선택된 콘텐츠를 상단에 표시하는 콘텐츠 목록 API"""
    try:
        chasi_id = request.POST.get('chasi_id')
        selected_ids = request.POST.getlist('selected_ids[]')  # 선택된 콘텐츠 ID들
        
        # 선택된 ID들을 정수로 변환
        selected_ids = [int(id) for id in selected_ids if id.isdigit()]
        
        # 1. 먼저 선택된 콘텐츠들을 가져옴 (사용자 제한 없음)
        selected_contents = []
        if selected_ids:
            selected_contents = list(Contents.objects.filter(
                id__in=selected_ids,
                is_active=True
            ).select_related('content_type').order_by('-created_at'))
        
        # 2. 사용자가 생성한 나머지 콘텐츠들을 가져옴 (선택된 것 제외)
        user_contents = Contents.objects.filter(
            created_by=request.user,
            is_active=True
        ).exclude(
            id__in=selected_ids  # 선택된 콘텐츠는 제외
        ).select_related('content_type').order_by('-created_at')[:50]
        
        # 3. 두 리스트를 합침 (선택된 것이 먼저)
        all_contents = selected_contents + list(user_contents)
        
        # 4. 결과 데이터 생성
        contents_data = []
        for content in all_contents:
            content_item = {
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name,
                'created_at': content.created_at.strftime('%Y.%m.%d'),
                'preview': content.get_preview(50),
                'is_selected': content.id in selected_ids,  # 선택 여부 표시
                'is_mine': content.created_by == request.user  # 본인 콘텐츠 여부
            }
            contents_data.append(content_item)
        
        return JsonResponse({
            'success': True,
            'contents': contents_data,
            'chasi_id': chasi_id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)