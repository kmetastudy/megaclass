# teacher/views/chasi_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse
from django.db import models
import json
from ..models import *
from ..forms import *

@login_required
def chasi_slide_add(request, chasi_id):
    """차시 슬라이드 추가"""
    chasi = get_object_or_404(Chasi, pk=chasi_id)
    
    if request.method == 'POST':
        # POST 요청에서 content_id 가져오기
        content_id = request.POST.get('content_id')
        if not content_id:
            messages.error(request, '콘텐츠를 선택해주세요.')
            return redirect('teacher:chasi_slide_add', chasi_id=chasi_id)
        
        try:
            content = Contents.objects.get(id=content_id, is_active=True)
            
            # 슬라이드 번호 자동 설정
            last_slide = ChasiSlide.objects.filter(chasi=chasi).order_by('-slide_number').first()
            slide_number = (last_slide.slide_number + 1) if last_slide else 1
            
            # 슬라이드 생성
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
    
    # GET 요청 또는 에러 발생 시
    context = {
        'chasi': chasi,
        'course': chasi.sub_chapter.chapter.course,
        'chapter': chasi.sub_chapter.chapter,
        'subchapter': chasi.sub_chapter,
        'content_types': ContentType.objects.filter(is_active=True),
        'available_contents': Contents.objects.filter(is_active=True).select_related('content_type')
    }
    
    return render(request, 'teacher/courses/chasis/slide_add.html', context)

@login_required
def chasi_slide_edit(request, slide_id):
    """차시 슬라이드 수정"""
    slide = get_object_or_404(ChasiSlide, pk=slide_id)
    chasi = slide.chasi
    
    if request.method == 'POST':
        form = ChasiSlideForm(request.POST, instance=slide)
        if form.is_valid():
            updated_slide = form.save(commit=False)
            # 콘텐츠가 변경된 경우 콘텐츠 타입도 업데이트
            if 'content' in form.changed_data:
                updated_slide.content_type = updated_slide.content.content_type
            updated_slide.save()
            
            messages.success(request, '슬라이드가 수정되었습니다.')
            return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)
    else:
        form = ChasiSlideForm(instance=slide)
    
    context = {
        'form': form,
        'slide': slide,
        'chasi': chasi,
        'course': chasi.sub_chapter.chapter.course,
        'chapter': chasi.sub_chapter.chapter,
        'subchapter': chasi.sub_chapter,
        'object': slide  # 템플릿 호환성을 위해
    }
    
    return render(request, 'teacher/courses/chasis/slide_edit.html', context)

@login_required
@require_POST
def chasi_slide_delete(request, slide_id):
    """차시 슬라이드 삭제"""
    slide = get_object_or_404(ChasiSlide, pk=slide_id)
    chasi = slide.chasi
    deleted_number = slide.slide_number
    
    # 슬라이드 삭제
    slide.delete()
    
    # 삭제된 슬라이드 이후의 번호들을 앞으로 당김
    ChasiSlide.objects.filter(
        chasi=chasi,
        slide_number__gt=deleted_number
    ).update(slide_number=models.F('slide_number') - 1)
    
    messages.success(request, '슬라이드가 삭제되었습니다.')
    
    # AJAX 요청인 경우 JSON 응답
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': '슬라이드가 삭제되었습니다.',
            'redirect_url': reverse('teacher:chasi_slide_manage', kwargs={'chasi_id': chasi.id})
        })
    
    return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)

@login_required
@require_POST
def reorder_slides(request, chasi_id):
    """슬라이드 순서 변경 API"""
    try:
        data = json.loads(request.body)
        slide_orders = data.get('slide_orders', [])
        
        # 순서 업데이트
        for item in slide_orders:
            ChasiSlide.objects.filter(
                id=item['slide_id'],
                chasi_id=chasi_id
            ).update(slide_number=item['order'])
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# 추가 유틸리티 함수들

@login_required
def chasi_slide_manage(request, chasi_id):
    """차시 슬라이드 관리 페이지"""
    chasi = get_object_or_404(Chasi, pk=chasi_id)
    slides = ChasiSlide.objects.filter(
        chasi=chasi
    ).select_related('content_type', 'content').order_by('slide_number')
    
    context = {
        'chasi': chasi,
        'course': chasi.sub_chapter.chapter.course,
        'chapter': chasi.sub_chapter.chapter,
        'subchapter': chasi.sub_chapter,
        'slides': slides
    }
    
    return render(request, 'teacher/courses/chasis/slide_manage.html', context)

@login_required
def chasi_preview(request, chasi_id):
    """차시 미리보기"""
    chasi = get_object_or_404(Chasi, pk=chasi_id)
    slides = ChasiSlide.objects.filter(
        chasi=chasi,
        is_active=True
    ).select_related('content_type', 'content').order_by('slide_number')
    
    total_time = sum(slide.estimated_time for slide in slides)
    
    context = {
        'chasi': chasi,
        'slides': slides,
        'total_slides': slides.count(),
        'total_time': total_time
    }
    
    return render(request, 'teacher/courses/chasis/preview.html', context)

# 슬라이드 복사 기능 (추가 기능)
@login_required
@require_POST
def copy_slide(request, slide_id):
    """슬라이드 복사"""
    original_slide = get_object_or_404(ChasiSlide, pk=slide_id)
    chasi = original_slide.chasi
    
    # 마지막 슬라이드 번호 가져오기
    last_slide = ChasiSlide.objects.filter(chasi=chasi).order_by('-slide_number').first()
    new_slide_number = (last_slide.slide_number + 1) if last_slide else 1
    
    # 슬라이드 복사
    new_slide = ChasiSlide.objects.create(
        chasi=chasi,
        slide_number=new_slide_number,
        slide_title=f"{original_slide.slide_title} (복사본)" if original_slide.slide_title else "복사된 슬라이드",
        content_type=original_slide.content_type,
        content=original_slide.content,
        instructor_notes=original_slide.instructor_notes,
        estimated_time=original_slide.estimated_time,
        is_active=original_slide.is_active
    )
    
    messages.success(request, '슬라이드가 복사되었습니다.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'slide_id': new_slide.id,
            'message': '슬라이드가 복사되었습니다.'
        })
    
    return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)

# 슬라이드 활성화/비활성화 토글
@login_required
@require_POST
def toggle_slide_active(request, slide_id):
    """슬라이드 활성화/비활성화 토글"""
    slide = get_object_or_404(ChasiSlide, pk=slide_id)
    slide.is_active = not slide.is_active
    slide.save(update_fields=['is_active'])
    
    status = "활성화" if slide.is_active else "비활성화"
    messages.success(request, f'슬라이드가 {status}되었습니다.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_active': slide.is_active,
            'message': f'슬라이드가 {status}되었습니다.'
        })
    
    return redirect('teacher:chasi_slide_manage', chasi_id=slide.chasi.id)