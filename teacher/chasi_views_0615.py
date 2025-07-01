# teacher/views/chasi_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db import models
import json

from .models import Chasi, ChasiSlide, Contents, ContentType
from .forms import ChasiSlideForm

@login_required
def chasi_slide_manage(request, chasi_id):
    """차시 슬라이드 관리 페이지"""
    chasi = get_object_or_404(Chasi, pk=chasi_id)
    
    # 권한 확인
    if chasi.sub_chapter.chapter.subject.teacher.user != request.user:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('teacher:dashboard')
    
    slides = ChasiSlide.objects.filter(
        chasi=chasi
    ).select_related('content_type', 'content').order_by('slide_number')
    
    context = {
        'chasi': chasi,
        'course': chasi.sub_chapter.chapter.subject,
        'chapter': chasi.sub_chapter.chapter,
        'subchapter': chasi.sub_chapter,
        'slides': slides
    }
    
    return render(request, 'teacher/courses/chasis/slide_manage.html', context)

@login_required
def chasi_slide_add(request, chasi_id):
    """차시 슬라이드 추가"""
    chasi = get_object_or_404(Chasi, pk=chasi_id)
    
    # 권한 확인
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
    
    # GET 요청
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
def chasi_slide_edit(request, slide_id):
    """차시 슬라이드 수정"""
    slide = get_object_or_404(ChasiSlide, pk=slide_id)
    chasi = slide.chasi
    
    # 권한 확인
    if chasi.sub_chapter.chapter.subject.teacher.user != request.user:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('teacher:dashboard')
    
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
        # 사용자의 콘텐츠만 선택 가능하도록
        form.fields['content'].queryset = Contents.objects.filter(
            created_by=request.user, 
            is_active=True
        )
    
    context = {
        'form': form,
        'slide': slide,
        'chasi': chasi,
        'course': chasi.sub_chapter.chapter.subject,
        'chapter': chasi.sub_chapter.chapter,
        'subchapter': chasi.sub_chapter,
        'object': slide
    }
    
    return render(request, 'teacher/courses/chasis/slide_edit.html', context)

@login_required
@require_POST
def chasi_slide_delete(request, slide_id):
    """차시 슬라이드 삭제"""
    slide = get_object_or_404(ChasiSlide, pk=slide_id)
    chasi = slide.chasi
    
    # 권한 확인
    if chasi.sub_chapter.chapter.subject.teacher.user != request.user:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
    
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
        chasi = get_object_or_404(Chasi, pk=chasi_id)
        
        # 권한 확인
        if chasi.sub_chapter.chapter.subject.teacher.user != request.user:
            return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
        
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

@login_required
def chasi_preview(request, chasi_id):
    """차시 미리보기"""
    chasi = get_object_or_404(Chasi, pk=chasi_id)
    
    # 권한 확인
    if chasi.sub_chapter.chapter.subject.teacher.user != request.user:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('teacher:dashboard')
    
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