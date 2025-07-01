# 완전한 코스 관리 시스템 🎓

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from datetime import datetime
import json

# 모델 import - 모두 teacher 앱으로 통일
from .models import (
    Course, Chapter, SubChapter, Chasi, ChasiSlide, 
    ContentType, Contents, CourseAssignment, ContentsAttached
)
from accounts.models import Teacher, Class, Student
from .forms import (
    CourseForm, ChapterForm, SubChapterForm, ChasiForm, 
    ChasiSlideForm,  ContentsForm
)
from .decorators import teacher_required
from .utils import get_course_statistics, get_course_progress
from django.db.models import Prefetch

# ========================================
# 코스 관리 뷰들
# ========================================
@login_required
@teacher_required
def course_list_view(request):
    """코스 목록"""
    teacher = request.user.teacher
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    courses = Course.objects.filter(teacher=teacher)
    
    # 디버깅을 위한 로그
    print(f"교사: {teacher}, 코스 수: {courses.count()}")
    
    if search_query:
        courses = courses.filter(
            Q(subject_name__icontains=search_query) |
            Q(target__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 코스별 통계 추가
    courses = courses.annotate(
        chapter_count=Count('chapters'),
        assignment_count=Count('assignments')
    ).order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 디버깅 정보 추가
    print(f"페이지 객체 리스트 수: {len(page_obj.object_list)}")
    for course in page_obj.object_list:
        print(f"코스: {course.subject_name}, 대단원: {course.chapter_count}, 할당: {course.assignment_count}")
    
    context = {
        'courses': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_courses': courses.count(),
    }
    
    return render(request, 'teacher/courses/list.html', context)


@login_required
@teacher_required
def course_list_view_0615(request):
    """코스 목록"""
    teacher = request.user.teacher
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    courses = Course.objects.filter(teacher=teacher)
    
    if search_query:
        courses = courses.filter(
            Q(subject_name__icontains=search_query) |
            Q(target__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 코스별 통계 추가
    courses = courses.annotate(
        chapter_count=Count('chapters'),
        assignment_count=Count('assignments')
    ).order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'courses': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_courses': courses.count(),
    }
    
    return render(request, 'teacher/courses/list.html', context)

@login_required
@teacher_required
def course_create_view(request):
    """코스 생성"""
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save(commit=False)
                    course.teacher = teacher
                    course.save()
                    
                    messages.success(request, f'코스 "{course.subject_name}"이 성공적으로 생성되었습니다.')
                    return redirect('teacher:course_detail', course_id=course.id)
                    
            except Exception as e:
                messages.error(request, f'코스 생성 중 오류가 발생했습니다: {str(e)}')
    else:
        form = CourseForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'teacher/courses/create.html', context)




@login_required
@teacher_required
def course_detail_view(request, course_id):
    """코스 상세 정보"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # Prefetch를 사용하여 관련 데이터를 미리 로드
    chapters = Chapter.objects.filter(subject=course).prefetch_related(
        'subchapters',
        'subchapters__chasis'
    ).order_by('chapter_order')
    
    # Python에서 카운트 계산
    chapters_with_counts = []
    for chapter in chapters:
        chapter.subchapter_count = chapter.subchapters.count()
        chapter.chasi_count = sum(sc.chasis.count() for sc in chapter.subchapters.all())
        chapters_with_counts.append(chapter)
    
    # 최근 활동
    recent_assignments = CourseAssignment.objects.filter(
        course=course
    ).select_related('assigned_class', 'assigned_student__user').order_by('-assigned_at')[:5]
    
    # 통계
    stats = get_course_statistics(course)
    progress = get_course_progress(course)
    
    context = {
        'course': course,
        'chapters': chapters_with_counts,
        'recent_assignments': recent_assignments,
        'stats': stats,
        'progress': progress,
    }
    
    return render(request, 'teacher/courses/detail.html', context)

@login_required
@teacher_required
def course_detail_view_0615(request, course_id):
    """코스 상세 정보"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # 코스 구조 정보
    chapters = Chapter.objects.filter(subject=course).annotate(
        subchapter_count=Count('subchapters'),
        chasi_count=Count('subchapters__chasis')
    ).order_by('chapter_order')
    
    # 최근 활동 - CourseAssignment 사용
    recent_assignments = CourseAssignment.objects.filter(
        course=course
    ).select_related('assigned_class', 'assigned_student__user').order_by('-assigned_at')[:5]
    
    # 통계
    stats = get_course_statistics(course)
    progress = get_course_progress(course)
    
    context = {
        'course': course,
        'chapters': chapters,
        'recent_assignments': recent_assignments,
        'stats': stats,
        'progress': progress,
    }
    
    return render(request, 'teacher/courses/detail.html', context)


@login_required
@teacher_required
def course_detail_view_0609(request, course_id):
    """코스 상세 정보"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # 코스 구조 정보
    chapters = Chapter.objects.filter(subject=course).annotate(
        subchapter_count=Count('subchapters'),
        chasi_count=Count('subchapters__chasis')
    ).order_by('chapter_order')
    
    # 최근 활동
    recent_assignments = CourseAssignment.objects.filter(
        course=course
    ).select_related('assigned_class', 'assigned_student').order_by('-assigned_at')[:5]
    
    # 통계
    stats = get_course_statistics(course)
    progress = get_course_progress(course)
    
    context = {
        'course': course,
        'chapters': chapters,
        'recent_assignments': recent_assignments,
        'stats': stats,
        'progress': progress,
    }
    
    return render(request, 'teacher/courses/detail.html', context)

@login_required
@teacher_required
def course_edit_view(request, course_id):
    """코스 수정"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'코스 "{course.subject_name}"이 수정되었습니다.')
            return redirect('teacher:course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    context = {
        'course': course,
        'form': form,
    }
    return render(request, 'teacher/courses/edit.html', context)

@login_required
@teacher_required
def course_delete_view(request, course_id):
    """코스 삭제"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    if request.method == 'POST':
        course_name = course.subject_name
        course.delete()
        messages.success(request, f'코스 "{course_name}"이 삭제되었습니다.')
        return redirect('teacher:course_list')
    
    context = {
        'course': course,
        'stats': get_course_statistics(course),
    }
    return render(request, 'teacher/courses/delete.html', context)

# ========================================
# 대단원(Chapter) 관리 뷰들
# ========================================
@login_required
@teacher_required
def chapter_list_view(request, course_id):
    """대단원 목록"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # distinct=True 추가
    chapters = Chapter.objects.filter(subject=course).annotate(
        subchapter_count=Count('subchapters', distinct=True),
        chasi_count=Count('subchapters__chasis', distinct=True)
    ).order_by('chapter_order')
    
    context = {
        'course': course,
        'chapters': chapters,
    }
    
    return render(request, 'teacher/courses/chapters/list.html', context)


@login_required
@teacher_required
def chapter_list_view_0615(request, course_id):
    """대단원 목록"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    chapters = Chapter.objects.filter(subject=course).annotate(
        subchapter_count=Count('subchapters'),
        chasi_count=Count('subchapters__chasis')
    ).order_by('chapter_order')
    
    context = {
        'course': course,
        'chapters': chapters,
    }
    
    return render(request, 'teacher/courses/chapters/list.html', context)


# courses.py의 chapter_create_view 수정
@login_required
@teacher_required
def chapter_create_view(request, course_id):
    """대단원 생성"""
    course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
    
    if request.method == 'POST':
        form = ChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.subject = course
            chapter.save()
            
            # AJAX 요청인 경우 JSON 응답
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '대단원이 생성되었습니다.',
                    'chapter': {
                        'id': chapter.id,
                        'title': chapter.chapter_title,
                        'order': chapter.chapter_order
                    }
                })
            
            messages.success(request, '대단원이 생성되었습니다.')
            return redirect('teacher:course_detail', course_id=course.id)
        else:
            # AJAX 요청인 경우 에러 JSON 응답
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0]
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
    else:
        form = ChapterForm()
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'teacher/courses/chapters/create.html', context)

@login_required
@teacher_required
def chapter_create_view_0616(request, course_id):
    """대단원 생성"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    if request.method == 'POST':
        form = ChapterForm(request.POST)
        if form.is_valid():
            try:
                chapter = form.save(commit=False)
                chapter.subject = course
                
                # 순서가 지정되지 않은 경우 자동 계산
                if not chapter.chapter_order:
                    last_chapter = Chapter.objects.filter(subject=course).order_by('-chapter_order').first()
                    chapter.chapter_order = (last_chapter.chapter_order + 1) if last_chapter else 1
                
                chapter.save()
                
                messages.success(request, f'대단원 "{chapter.chapter_title}"이 생성되었습니다.')
                return redirect('teacher:chapter_list', course_id=course.id)
                
            except Exception as e:
                messages.error(request, f'대단원 생성 중 오류가 발생했습니다: {str(e)}')
    else:
        # 다음 순서 제안
        last_chapter = Chapter.objects.filter(subject=course).order_by('-chapter_order').first()
        suggested_order = (last_chapter.chapter_order + 1) if last_chapter else 1
        
        form = ChapterForm(initial={'chapter_order': suggested_order})
    
    context = {
        'course': course,
        'form': form,
    }
    
    return render(request, 'teacher/courses/chapters/create.html', context)

@login_required
@teacher_required
def chapter_edit_view(request, chapter_id):
    """대단원 수정"""
    teacher = request.user.teacher
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=teacher)
    
    if request.method == 'POST':
        form = ChapterForm(request.POST, instance=chapter)
        if form.is_valid():
            form.save()
            messages.success(request, f'대단원 "{chapter.chapter_title}"이 수정되었습니다.')
            return redirect('teacher:chapter_list', course_id=chapter.subject.id)
    else:
        form = ChapterForm(instance=chapter)
    
    context = {
        'chapter': chapter,
        'course': chapter.subject,
        'form': form,
    }
    return render(request, 'teacher/courses/chapters/edit.html', context)

from django.views.decorators.http import require_http_methods, require_POST, require_GET

# chapter_delete_view 수정
@login_required
@teacher_required
@require_POST
def chapter_delete_view(request, chapter_id):
    """대단원 삭제"""
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=request.user.teacher)
    course_id = chapter.subject.id
    
    try:
        chapter.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '대단원이 삭제되었습니다.'
            })
        
        messages.success(request, '대단원이 삭제되었습니다.')
        return redirect('teacher:course_detail', course_id=course_id)
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        messages.error(request, f'삭제 중 오류가 발생했습니다: {str(e)}')
        return redirect('teacher:course_detail', course_id=course_id)

@login_required
@teacher_required
def chapter_delete_view_0616(request, chapter_id):
    """대단원 삭제"""
    teacher = request.user.teacher
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=teacher)
    course = chapter.subject
    
    if request.method == 'POST':
        chapter_title = chapter.chapter_title
        chapter.delete()
        messages.success(request, f'대단원 "{chapter_title}"이 삭제되었습니다.')
        return redirect('teacher:chapter_list', course_id=course.id)
    
    subchapter_count = chapter.subchapters.count()
    chasi_count = sum(sc.chasis.count() for sc in chapter.subchapters.all())
    
    context = {
        'chapter': chapter,
        'course': course,
        'subchapter_count': subchapter_count,
        'chasi_count': chasi_count,
    }
    return render(request, 'teacher/courses/chapters/delete.html', context)

# ========================================
# 소단원(SubChapter) 관리 뷰들
# ========================================

@login_required
@teacher_required
def subchapter_list_view(request, chapter_id):
    """소단원 목록"""
    teacher = request.user.teacher
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=teacher)
    
    subchapters = SubChapter.objects.filter(chapter=chapter).annotate(
        chasi_count=Count('chasis')
    ).order_by('sub_chapter_order')
    
    context = {
        'chapter': chapter,
        'course': chapter.subject,
        'subchapters': subchapters,
    }
    
    return render(request, 'teacher/courses/subchapters/list.html', context)

# subchapter_create_view 수정
@login_required
@teacher_required
def subchapter_create_view(request, chapter_id):
    """소단원 생성"""
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=request.user.teacher)
    
    if request.method == 'POST':
        form = SubChapterForm(request.POST)
        if form.is_valid():
            subchapter = form.save(commit=False)
            subchapter.chapter = chapter
            subchapter.subject = chapter.subject
            subchapter.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '소단원이 생성되었습니다.',
                    'subchapter': {
                        'id': subchapter.id,
                        'title': subchapter.sub_chapter_title,
                        'order': subchapter.sub_chapter_order
                    }
                })
            
            messages.success(request, '소단원이 생성되었습니다.')
            return redirect('teacher:course_detail', course_id=chapter.subject.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': '입력값을 확인해주세요.'
                }, status=400)
    else:
        form = SubChapterForm()
    
    context = {
        'form': form,
        'chapter': chapter,
        'course': chapter.subject,
    }
    return render(request, 'teacher/courses/subchapters/create.html', context)

@login_required
@teacher_required
def subchapter_create_view_0616(request, chapter_id):
    """소단원 생성"""
    teacher = request.user.teacher
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=teacher)
    
    if request.method == 'POST':
        form = SubChapterForm(request.POST)
        if form.is_valid():
            try:
                subchapter = form.save(commit=False)
                subchapter.subject = chapter.subject
                subchapter.chapter = chapter
                
                # 순서가 지정되지 않은 경우 자동 계산
                if not subchapter.sub_chapter_order:
                    last_subchapter = SubChapter.objects.filter(chapter=chapter).order_by('-sub_chapter_order').first()
                    subchapter.sub_chapter_order = (last_subchapter.sub_chapter_order + 1) if last_subchapter else 1
                
                subchapter.save()
                
                messages.success(request, f'소단원 "{subchapter.sub_chapter_title}"이 생성되었습니다.')
                return redirect('teacher:subchapter_list', chapter_id=chapter.id)
                
            except Exception as e:
                messages.error(request, f'소단원 생성 중 오류가 발생했습니다: {str(e)}')
    else:
        # 다음 순서 제안
        last_subchapter = SubChapter.objects.filter(chapter=chapter).order_by('-sub_chapter_order').first()
        suggested_order = (last_subchapter.sub_chapter_order + 1) if last_subchapter else 1
        
        form = SubChapterForm(initial={'sub_chapter_order': suggested_order})
    
    context = {
        'chapter': chapter,
        'course': chapter.subject,
        'form': form,
    }
    
    return render(request, 'teacher/courses/subchapters/create.html', context)

@login_required
@teacher_required
def subchapter_edit_view(request, subchapter_id):
    """소단원 수정"""
    teacher = request.user.teacher
    subchapter = get_object_or_404(SubChapter, id=subchapter_id, subject__teacher=teacher)
    
    if request.method == 'POST':
        form = SubChapterForm(request.POST, instance=subchapter)
        if form.is_valid():
            form.save()
            messages.success(request, f'소단원 "{subchapter.sub_chapter_title}"이 수정되었습니다.')
            return redirect('teacher:subchapter_list', chapter_id=subchapter.chapter.id)
    else:
        form = SubChapterForm(instance=subchapter)
    
    context = {
        'subchapter': subchapter,
        'chapter': subchapter.chapter,
        'course': subchapter.subject,
        'form': form,
    }
    return render(request, 'teacher/courses/subchapters/edit.html', context)

@login_required
@teacher_required
def subchapter_delete_view(request, subchapter_id):
    """소단원 삭제"""
    teacher = request.user.teacher
    subchapter = get_object_or_404(SubChapter, id=subchapter_id, subject__teacher=teacher)
    chapter = subchapter.chapter
    
    if request.method == 'POST':
        subchapter_title = subchapter.sub_chapter_title
        subchapter.delete()
        messages.success(request, f'소단원 "{subchapter_title}"이 삭제되었습니다.')
        return redirect('teacher:subchapter_list', chapter_id=chapter.id)
    
    chasi_count = subchapter.chasis.count()
    
    context = {
        'subchapter': subchapter,
        'chapter': chapter,
        'course': subchapter.subject,
        'chasi_count': chasi_count,
    }
    return render(request, 'teacher/courses/subchapters/delete.html', context)

# ========================================
# 차시(Chasi) 관리 뷰들
# ========================================

@login_required
@teacher_required
def chasi_list_view(request, subchapter_id):
    """차시 목록"""
    teacher = request.user.teacher
    subchapter = get_object_or_404(SubChapter, id=subchapter_id, subject__teacher=teacher)
    
    chasis = Chasi.objects.filter(sub_chapter=subchapter).annotate(
    slide_count=Count('teacher_slides')
    ).order_by('chasi_order')
    
    context = {
        'subchapter': subchapter,
        'chapter': subchapter.chapter,
        'course': subchapter.subject,
        'chasis': chasis,
    }
    
    return render(request, 'teacher/courses/chasis/list.html', context)

@login_required
@teacher_required
def chasi_create_view(request, subchapter_id):
    """차시 생성"""
    teacher = request.user.teacher
    subchapter = get_object_or_404(SubChapter, id=subchapter_id, subject__teacher=teacher)
    
    if request.method == 'POST':
        form = ChasiForm(request.POST)
        if form.is_valid():
            try:
                chasi = form.save(commit=False)
                chasi.subject = subchapter.subject
                chasi.chapter = subchapter.chapter
                chasi.sub_chapter = subchapter
                chasi.chapter_order = subchapter.chapter.chapter_order
                chasi.sub_chapter_order = subchapter.sub_chapter_order
                
                # 순서가 지정되지 않은 경우 자동 계산
                if not chasi.chasi_order:
                    last_chasi = Chasi.objects.filter(sub_chapter=subchapter).order_by('-chasi_order').first()
                    chasi.chasi_order = (last_chasi.chasi_order + 1) if last_chasi else 1
                
                chasi.save()
                
                messages.success(request, f'차시 "{chasi.chasi_title}"이 생성되었습니다.')
                return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)
                
            except Exception as e:
                messages.error(request, f'차시 생성 중 오류가 발생했습니다: {str(e)}')
    else:
        # 다음 순서 제안
        last_chasi = Chasi.objects.filter(sub_chapter=subchapter).order_by('-chasi_order').first()
        suggested_order = (last_chasi.chasi_order + 1) if last_chasi else 1
        
        form = ChasiForm(initial={'chasi_order': suggested_order})
    
    context = {
        'subchapter': subchapter,
        'chapter': subchapter.chapter,
        'course': subchapter.subject,
        'form': form,
    }
    
    return render(request, 'teacher/courses/chasis/create.html', context)

@login_required
@teacher_required
def chasi_edit_view(request, chasi_id):
    """차시 수정"""
    teacher = request.user.teacher
    chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
    
    if request.method == 'POST':
        form = ChasiForm(request.POST, instance=chasi)
        if form.is_valid():
            form.save()
            messages.success(request, f'차시 "{chasi.chasi_title}"이 수정되었습니다.')
            return redirect('teacher:chasi_list', subchapter_id=chasi.sub_chapter.id)
    else:
        form = ChasiForm(instance=chasi)
    
    context = {
        'chasi': chasi,
        'subchapter': chasi.sub_chapter,
        'chapter': chasi.chapter,
        'course': chasi.subject,
        'form': form,
    }
    return render(request, 'teacher/courses/chasis/edit.html', context)

@login_required
@teacher_required
def chasi_delete_view(request, chasi_id):
    """차시 삭제"""
    teacher = request.user.teacher
    chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
    subchapter = chasi.sub_chapter
    
    if request.method == 'POST':
        chasi_title = chasi.chasi_title
        chasi.delete()
        messages.success(request, f'차시 "{chasi_title}"이 삭제되었습니다.')
        return redirect('teacher:chasi_list', subchapter_id=subchapter.id)
    
    slide_count = chasi.teacher_slides.count()
    
    context = {
        'chasi': chasi,
        'subchapter': subchapter,
        'chapter': chasi.chapter,
        'course': chasi.subject,
        'slide_count': slide_count,
    }
    return render(request, 'teacher/courses/chasis/delete.html', context)

# ========================================
# 차시 슬라이드 관리 뷰들
# ========================================
@login_required
@teacher_required
def chasi_slide_manage_view(request, chasi_id):
    """차시 슬라이드 관리"""
    
    chasi = get_object_or_404(
        Chasi.objects.select_related('sub_chapter__chapter__subject'),
        id=chasi_id,
    )
    
    # 권한 확인 추가
    if chasi.sub_chapter.chapter.subject.teacher != request.user.teacher:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('teacher:dashboard')
    
    slides = ChasiSlide.objects.filter(chasi=chasi).select_related(
        'content_type', 'content'
    ).order_by('slide_number')
    
    # 사용 가능한 컨텐츠 타입들
    content_types = ContentType.objects.filter(is_active=True)
    
    # ★★★ 수정: 교사 본인의 콘텐츠만 가져오도록 변경 ★★★
    available_contents = Contents.objects.filter(
        created_by=request.user,  # 교사 본인이 생성한 것만
        is_active=True
    ).select_related('content_type').order_by('-created_at')[:20]
    # 공개 콘텐츠(is_public=True)를 제외했습니다
    
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
def chasi_slide_manage_view_0621(request, chasi_id):
    """차시 슬라이드 관리"""
    
    chasi = get_object_or_404(
        Chasi.objects.select_related('sub_chapter__chapter__subject'),
        id=chasi_id,
        
    )
    
    slides = ChasiSlide.objects.filter(chasi=chasi).select_related(
        'content_type', 'content'
    ).order_by('slide_number')
    
    # 사용 가능한 컨텐츠 타입들
    content_types = ContentType.objects.filter(is_active=True)
    
    # 사용 가능한 컨텐츠들
    available_contents = Contents.objects.filter(
        created_by=request.user,
        is_active=True
    ).select_related('content_type').order_by('-created_at')[:20]
    
    context = {
        'chasi': chasi,
        'subchapter': chasi.sub_chapter,
        'chapter': chasi.sub_chapter.chapter,
        'course': chasi.sub_chapter.chapter.subject,  # 중요: subject가 course
        'slides': slides,
        'content_types': content_types,
        'available_contents': available_contents,
    }
    
    return render(request, 'teacher/courses/chasis/slide_manage.html', context)

@login_required
@teacher_required
def chasi_slide_manage_view_0601(request, chasi_id):
    """차시 슬라이드 관리"""
    teacher = request.user.teacher
    chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
    
    slides = ChasiSlide.objects.filter(chasi=chasi).select_related(
        'content_type', 'content'
    ).order_by('slide_number')
    
    # 사용 가능한 컨텐츠 타입들
    content_types = ContentType.objects.filter(is_active=True)
    
    # 사용 가능한 컨텐츠들 (교사 것 + 공개된 것)
    available_contents = Contents.objects.filter(
        Q(created_by=teacher) | Q(is_public=True)
    ).select_related('content_type').order_by('-created_at')[:20]
    
    context = {
        'chasi': chasi,
        'subchapter': chasi.sub_chapter,
        'chapter': chasi.chapter,
        'course': chasi.subject,
        'slides': slides,
        'content_types': content_types,
        'available_contents': available_contents,
    }
    
    return render(request, 'teacher/courses/chasis/slide_manage.html', context)


@login_required
@teacher_required
def chasi_slide_add_view(request, chasi_id):
    """차시에 슬라이드 추가"""
    # chasi 권한 확인 - teacher 변수 사용하지 않고 처리
    chasi = get_object_or_404(
        Chasi.objects.select_related('sub_chapter__chapter__subject__teacher'),
        id=chasi_id
    )
    
    # 권한 확인
    if chasi.sub_chapter.chapter.subject.teacher.user != request.user:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('teacher:dashboard')
    
    if request.method == 'POST':
        # POST 처리 로직
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
    
    # GET 요청 또는 에러 발생 시
    # 사용 가능한 콘텐츠 타입들
    content_types = ContentType.objects.filter(is_active=True)
    
    # 사용 가능한 콘텐츠들 - request.user 사용
    available_contents = Contents.objects.filter(
        created_by=request.user,  # teacher가 아닌 request.user
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
def chasi_slide_add_view_0601(request, chasi_id):
    """차시 슬라이드 추가"""
    teacher = request.user.teacher
    chasi = get_object_or_404(Chasi, id=chasi_id)
    
    if request.method == 'POST':
        form = ChasiSlideForm(request.POST)
        if form.is_valid():
            try:
                slide = form.save(commit=False)
                slide.chasi = chasi
                
                # 슬라이드 번호가 지정되지 않은 경우 자동 계산
                if not slide.slide_number:
                    last_slide = ChasiSlide.objects.filter(chasi=chasi).order_by('-slide_number').first()
                    slide.slide_number = (last_slide.slide_number + 1) if last_slide else 1
                
                slide.save()
                
                messages.success(request, f'슬라이드가 추가되었습니다.')
                return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)
                
            except Exception as e:
                messages.error(request, f'슬라이드 추가 중 오류가 발생했습니다: {str(e)}')
    else:
        # 다음 슬라이드 번호 제안
        last_slide = ChasiSlide.objects.filter(chasi=chasi).order_by('-slide_number').first()
        suggested_number = (last_slide.slide_number + 1) if last_slide else 1
        
        form = ChasiSlideForm(initial={'slide_number': suggested_number})
    
    # 사용 가능한 컨텐츠들
    content_types = ContentType.objects.filter(is_active=True)
    available_contents = Contents.objects.filter(
        Q(created_by=teacher) | Q(is_public=True)
    ).select_related('content_type').order_by('-created_at')
    
    context = {
        'chasi': chasi,
        'form': form,
        'content_types': content_types,
        'available_contents': available_contents,
    }
    
    return render(request, 'teacher/courses/chasis/slide_add.html', context)

@login_required
@teacher_required
def chasi_slide_edit_view(request, slide_id):
    """슬라이드 수정"""
    teacher = request.user.teacher
    slide = get_object_or_404(ChasiSlide, id=slide_id, chasi__subject__teacher=teacher)
    
    if request.method == 'POST':
        form = ChasiSlideForm(request.POST, instance=slide)
        if form.is_valid():
            form.save()
            messages.success(request, '슬라이드가 수정되었습니다.')
            return redirect('teacher:chasi_slide_manage', chasi_id=slide.chasi.id)
    else:
        form = ChasiSlideForm(instance=slide)
    
    context = {
        'slide': slide,
        'chasi': slide.chasi,
        'form': form,
    }
    return render(request, 'teacher/courses/chasis/slide_edit.html', context)

@login_required
@teacher_required
def chasi_slide_delete_view(request, slide_id):
    """슬라이드 삭제"""
    teacher = request.user.teacher
    slide = get_object_or_404(ChasiSlide, id=slide_id, chasi__subject__teacher=teacher)
    chasi = slide.chasi
    
    if request.method == 'POST':
        slide.delete()
        
        # 슬라이드 번호 재정렬
        remaining_slides = ChasiSlide.objects.filter(chasi=chasi).order_by('slide_number')
        for idx, remaining_slide in enumerate(remaining_slides, 1):
            remaining_slide.slide_number = idx
            remaining_slide.save()
        
        messages.success(request, '슬라이드가 삭제되었습니다.')
        return redirect('teacher:chasi_slide_manage', chasi_id=chasi.id)
    
    context = {
        'slide': slide,
        'chasi': chasi,
    }
    return render(request, 'teacher/courses/chasis/slide_delete.html', context)

# ========================================
# 코스 할당 관리 뷰들
# ========================================
@login_required
@teacher_required
def course_assign_view(request, course_id):
    """코스 할당 (수정된 버전)"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    if request.method == 'POST':
        try:
            assign_type = request.POST.get('assign_type')
            due_date_str = request.POST.get('due_date')
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M') if due_date_str else None
            
            with transaction.atomic():
                if assign_type == 'class':
                    class_ids = request.POST.getlist('class_ids')
                    if not class_ids:
                        messages.warning(request, '할당할 학급을 선택해주세요.')
                        return redirect('teacher:course_assign', course_id=course.id)
                    
                    for class_id in class_ids:
                        # ★★★ [수정] 할당할 학급의 소유권 확인 ★★★
                        class_obj = get_object_or_404(Class, id=class_id, teachers=teacher)
                        CourseAssignment.objects.update_or_create(
                            course=course, assigned_class=class_obj,
                            defaults={'due_date': due_date}
                        )
                    messages.success(request, f'{len(class_ids)}개 학급에 코스가 할당/업데이트되었습니다.')

                elif assign_type == 'student':
                    student_ids = request.POST.getlist('student_ids')
                    if not student_ids:
                        messages.warning(request, '할당할 학생을 선택해주세요.')
                        return redirect('teacher:course_assign', course_id=course.id)

                    for student_id in student_ids:
                        # ★★★ [수정] 할당할 학생의 소유권 확인 ★★★
                        student = get_object_or_404(Student, id=student_id, school_class__teachers=teacher)
                        CourseAssignment.objects.update_or_create(
                            course=course, assigned_student=student,
                            defaults={'due_date': due_date}
                        )
                    messages.success(request, f'{len(student_ids)}명 학생에게 코스가 할당/업데이트되었습니다.')
            
            return redirect('teacher:course_detail', course_id=course.id)
            
        except Exception as e:
            messages.error(request, f'코스 할당 중 오류가 발생했습니다: {str(e)}')
            return redirect('teacher:course_assign', course_id=course.id)
    
    # GET 요청 처리
    # ★★★ [수정] 교사가 속한 학급 및 학생 목록만 가져오도록 변경 ★★★
    classes = Class.objects.filter(teachers=teacher).order_by('name')
    students = Student.objects.filter(
        school_class__teachers=teacher
    ).select_related('user', 'school_class').order_by('school_class__name', 'user__first_name')
    
    assigned_classes = list(CourseAssignment.objects.filter(course=course, assigned_class__isnull=False).values_list('assigned_class_id', flat=True))
    assigned_students = list(CourseAssignment.objects.filter(course=course, assigned_student__isnull=False).values_list('assigned_student_id', flat=True))
    
    context = {
        'course': course,
        'classes': classes,
        'students': students,
        'assigned_classes': assigned_classes,
        'assigned_students': assigned_students,
    }
    
    return render(request, 'teacher/courses/assign.html', context)



@login_required
@teacher_required
def course_assign_view_0608(request, course_id):
    """코스 할당"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    if request.method == 'POST':
        try:
            assign_type = request.POST.get('assign_type')  # 'class' or 'student'
            due_date = request.POST.get('due_date')  # 직접 POST에서 가져옴
            
            # due_date가 문자열로 전달되므로 datetime 객체로 변환
            if due_date:
                from datetime import datetime
                due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            else:
                due_date = None
            
            with transaction.atomic():
                if assign_type == 'class':
                    class_ids = request.POST.getlist('class_ids')
                    if not class_ids:
                        messages.warning(request, '할당할 학급을 선택해주세요.')
                        return redirect('teacher:course_assign', course_id=course.id)
                    
                    assigned_count = 0
                    for class_id in class_ids:
                        class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
                        assignment, created = CourseAssignment.objects.get_or_create(
                            course=course,
                            assigned_class=class_obj,
                            defaults={'due_date': due_date}
                        )
                        if created:
                            assigned_count += 1
                    
                    if assigned_count > 0:
                        messages.success(request, f'{assigned_count}개 학급에 코스가 할당되었습니다.')
                    else:
                        messages.info(request, '선택한 학급들은 이미 할당되어 있습니다.')
                
                elif assign_type == 'student':
                    student_ids = request.POST.getlist('student_ids')
                    if not student_ids:
                        messages.warning(request, '할당할 학생을 선택해주세요.')
                        return redirect('teacher:course_assign', course_id=course.id)
                    
                    assigned_count = 0
                    for student_id in student_ids:
                        student = get_object_or_404(Student, id=student_id, school_class__teachers=teacher)
                        assignment, created = CourseAssignment.objects.get_or_create(
                            course=course,
                            assigned_student=student,
                            defaults={'due_date': due_date}
                        )
                        if created:
                            assigned_count += 1
                    
                    if assigned_count > 0:
                        messages.success(request, f'{assigned_count}명 학생에게 코스가 할당되었습니다.')
                    else:
                        messages.info(request, '선택한 학생들은 이미 할당되어 있습니다.')
                else:
                    messages.error(request, '잘못된 할당 타입입니다.')
                    return redirect('teacher:course_assign', course_id=course.id)
            
            return redirect('teacher:course_detail', course_id=course.id)
            
        except ValueError as e:
            messages.error(request, '날짜 형식이 올바르지 않습니다.')
            return redirect('teacher:course_assign', course_id=course.id)
        except Exception as e:
            messages.error(request, f'코스 할당 중 오류가 발생했습니다: {str(e)}')
            return redirect('teacher:course_assign', course_id=course.id)
    
    # GET 요청 처리
    # 할당 가능한 학급들과 학생들
    classes = Class.objects.filter(teacher=teacher).order_by('name')
    students = Student.objects.filter(
        school_class__teachers=teacher
    ).select_related('user', 'school_class').order_by('school_class__name', 'user__first_name')
    
    # 이미 할당된 항목들
    assigned_classes = list(CourseAssignment.objects.filter(
        course=course, 
        assigned_class__isnull=False
    ).values_list('assigned_class_id', flat=True))
    
    assigned_students = list(CourseAssignment.objects.filter(
        course=course, 
        assigned_student__isnull=False
    ).values_list('assigned_student_id', flat=True))
    
    context = {
        'course': course,
        'classes': classes,
        'students': students,
        'assigned_classes': assigned_classes,
        'assigned_students': assigned_students,
    }
    
    return render(request, 'teacher/courses/assign.html', context)


# ========================================
# 컨텐츠 라이브러리 뷰들
# ========================================

@login_required
@teacher_required
def content_library_view(request):
    """컨텐츠 라이브러리"""
    teacher = request.user.teacher
    
    # 필터링
    content_type_id = request.GET.get('content_type')
    difficulty = request.GET.get('difficulty')
    search_query = request.GET.get('search', '')
    
    # 교사 본인의 컨텐츠 + 공개된 컨텐츠
    contents = Contents.objects.filter(
        Q(created_by=teacher) | Q(is_public=True)
    )
    
    if content_type_id:
        contents = contents.filter(content_type_id=content_type_id)
    
    if difficulty:
        contents = contents.filter(difficulty_level=difficulty)
    
    if search_query:
        contents = contents.filter(
            Q(title__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # 페이지네이션
    paginator = Paginator(contents.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 컨텐츠 타입들
    content_types = ContentType.objects.filter(is_active=True)
    
    context = {
        'contents': page_obj.object_list,
        'page_obj': page_obj,
        'content_types': content_types,
        'search_query': search_query,
        'selected_content_type': content_type_id,
        'selected_difficulty': difficulty,
    }
    
    return render(request, 'teacher/content_library.html', context)

@login_required
@teacher_required
def content_create_view(request):
    """컨텐츠 생성"""
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = ContentsForm(request.POST)
        if form.is_valid():
            try:
                content = form.save(commit=False)
                content.created_by = teacher
                content.save()
                
                messages.success(request, f'컨텐츠 "{content.title}"이 생성되었습니다.')
                return redirect('teacher:content_library')
                
            except Exception as e:
                messages.error(request, f'컨텐츠 생성 중 오류가 발생했습니다: {str(e)}')
    else:
        form = ContentsForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'teacher/contents/create.html', context)

# ========================================
# 미리보기 및 플레이어 뷰들
# ========================================

@login_required
@teacher_required
def chasi_preview_view(request, chasi_id):
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

@login_required
@teacher_required
def slide_content_view(request, slide_id):
    """개별 슬라이드 컨텐츠 뷰"""
    teacher = request.user.teacher
    slide = get_object_or_404(ChasiSlide, id=slide_id, chasi__subject__teacher=teacher)
    
    # 조회수 증가
    slide.content.view_count += 1
    slide.content.save(update_fields=['view_count'])
    
    context = {
        'slide': slide,
        'content': slide.content,
        'chasi': slide.chasi,
    }
    
    return render(request, 'teacher/courses/slide_content.html', context)

# ========================================
# 일괄 작업 뷰들
# ========================================

@login_required
@teacher_required
def bulk_chapter_create_view(request, course_id):
    """대단원 일괄 생성"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    if request.method == 'POST':
        try:
            chapter_data = json.loads(request.POST.get('chapter_data', '[]'))
            
            with transaction.atomic():
                for idx, data in enumerate(chapter_data):
                    Chapter.objects.create(
                        subject=course,
                        chapter_title=data['title'],
                        chapter_order=idx + 1,
                        description=data.get('description', '')
                    )
            
            messages.success(request, f'{len(chapter_data)}개의 대단원이 생성되었습니다.')
            return redirect('teacher:chapter_list', course_id=course.id)
            
        except Exception as e:
            messages.error(request, f'일괄 생성 중 오류가 발생했습니다: {str(e)}')
    
    context = {
        'course': course,
    }
    return render(request, 'teacher/courses/chapters/bulk_create.html', context)

# ========================================
# API 뷰들
# ========================================

@login_required
@teacher_required
def api_course_structure(request, course_id):
    """코스 구조 API - 수정된 버전"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    try:
        structure = {
            'course': {
                'id': course.id,
                'subject_name': course.subject_name,
                'target': course.target
            },
            'chapters': []
        }
        
        chapters = Chapter.objects.filter(subject=course).order_by('chapter_order')
        for chapter in chapters:
            chapter_data = {
                'id': chapter.id,
                'title': chapter.chapter_title,
                'order': chapter.chapter_order,
                'subchapters': []
            }
            
            subchapters = SubChapter.objects.filter(chapter=chapter).order_by('sub_chapter_order')
            for subchapter in subchapters:
                subchapter_data = {
                    'id': subchapter.id,
                    'title': subchapter.sub_chapter_title,
                    'order': subchapter.sub_chapter_order,
                    'chasis': []
                }
                
                chasis = Chasi.objects.filter(sub_chapter=subchapter).order_by('chasi_order')
                for chasi in chasis:
                    slide_count = ChasiSlide.objects.filter(chasi=chasi).count()
                    chasi_data = {
                        'id': chasi.id,
                        'title': chasi.chasi_title,
                        'order': chasi.chasi_order,
                        'slide_count': slide_count
                    }
                    subchapter_data['chasis'].append(chasi_data)
                
                chapter_data['subchapters'].append(subchapter_data)
            
            structure['chapters'].append(chapter_data)
        
        return JsonResponse({'success': True, 'structure': structure})
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in api_course_structure: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@teacher_required
def api_slide_reorder(request, chasi_id):
    """슬라이드 순서 변경 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    teacher = request.user.teacher
    chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
    
    try:
        data = json.loads(request.body)
        slide_orders = data.get('slide_orders', [])
        
        with transaction.atomic():
            for item in slide_orders:
                slide_id = item['slide_id']
                new_order = item['order']
                ChasiSlide.objects.filter(id=slide_id, chasi=chasi).update(slide_number=new_order)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@teacher_required
@require_http_methods(["POST"])
def api_toggle_course_status(request, course_id):
    """코스 활성/비활성 토글"""
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        course.is_active = not course.is_active
        course.save()
        
        return JsonResponse({
            'success': True,
            'is_active': course.is_active,
            'message': f'코스가 {"활성화" if course.is_active else "비활성화"}되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@teacher_required
@require_http_methods(["POST"])
def api_toggle_chasi_publish(request, chasi_id):
    """차시 공개/비공개 토글"""
    try:
        chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=request.user.teacher)
        chasi.is_published = not chasi.is_published
        chasi.save()
        
        return JsonResponse({
            'success': True,
            'is_published': chasi.is_published,
            'message': f'차시가 {"공개" if chasi.is_published else "비공개"}되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@teacher_required
def api_course_quick_stats(request, course_id):
    """코스 빠른 통계 API"""
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        stats = get_course_statistics(course)
        progress = get_course_progress(course)
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'progress': round(progress, 1)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@teacher_required
def api_search_contents(request):
    """컨텐츠 검색 API"""
    teacher = request.user.teacher
    
    try:
        query = request.GET.get('q', '')
        content_type = request.GET.get('type', '')
        difficulty = request.GET.get('difficulty', '')
        
        contents = Contents.objects.filter(
            Q(created_by=teacher) | Q(is_public=True)
        )
        
        if query:
            contents = contents.filter(
                Q(title__icontains=query) |
                Q(tags__icontains=query)
            )
        
        if content_type:
            contents = contents.filter(content_type_id=content_type)
        
        if difficulty:
            contents = contents.filter(difficulty_level=difficulty)
        
        results = []
        for content in contents[:20]:
            results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name,
                'difficulty': content.get_difficulty_level_display(),
                'estimated_time': content.estimated_time,
                'preview': content.page[:100] + '...' if len(content.page) > 100 else content.page
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

@login_required
@teacher_required
def course_detail_onepage_view(request, course_id):
    """코스 원페이지 통합 관리 뷰"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # 통계
    stats = get_course_statistics(course)
    
    context = {
        'course': course,
        'stats': stats,
    }
    
    return render(request, 'teacher/courses/course_detail_onepage.html', context)

# API Views
@login_required
@teacher_required
def api_course_detail(request, course_id):
    """코스 상세 정보 API"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    data = {
        'id': course.id,
        'subject_name': course.subject_name,
        'target': course.target,
        'description': course.description,
        'stats': get_course_statistics(course),
    }
    
    return JsonResponse(data)

@login_required
@teacher_required
def api_chapter_detail(request, chapter_id):
    """대단원 상세 정보 API"""
    teacher = request.user.teacher
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=teacher)
    
    subchapters = SubChapter.objects.filter(chapter=chapter).annotate(
        chasi_count=Count('chasis')
    ).order_by('sub_chapter_order')
    
    data = {
        'id': chapter.id,
        'chapter_title': chapter.chapter_title,
        'chapter_order': chapter.chapter_order,
        'description': chapter.description,
        'subchapters': [{
            'id': sc.id,
            'title': sc.sub_chapter_title,
            'order': sc.sub_chapter_order,
            'chasi_count': sc.chasi_count
        } for sc in subchapters]
    }
    
    return JsonResponse(data)

@login_required
@teacher_required
def api_subchapter_detail(request, subchapter_id):
    """소단원 상세 정보 API"""
    teacher = request.user.teacher
    subchapter = get_object_or_404(SubChapter, id=subchapter_id, subject__teacher=teacher)
    
    chasis = Chasi.objects.filter(sub_chapter=subchapter).annotate(
        slide_count=Count('teacher_slides')
    ).order_by('chasi_order')
    
    data = {
        'id': subchapter.id,
        'sub_chapter_title': subchapter.sub_chapter_title,
        'sub_chapter_order': subchapter.sub_chapter_order,
        'description': subchapter.description,
        'chasis': [{
            'id': ch.id,
            'title': ch.chasi_title,
            'order': ch.chasi_order,
            'slide_count': ch.slide_count,
            'duration': ch.duration_minutes
        } for ch in chasis]
    }
    
    return JsonResponse(data)

@login_required
@teacher_required
def api_chasi_detail(request, chasi_id):
    """차시 상세 정보 API"""
    teacher = request.user.teacher
    chasi = get_object_or_404(Chasi, id=chasi_id, subject__teacher=teacher)
    
    slides = ChasiSlide.objects.filter(chasi=chasi).select_related(
        'content_type', 'content'
    ).order_by('slide_number')
    
    data = {
        'id': chasi.id,
        'chasi_title': chasi.chasi_title,
        'chasi_order': chasi.chasi_order,
        'description': chasi.description,
        'learning_objectives': chasi.learning_objectives,
        'duration_minutes': chasi.duration_minutes,
        'slides': [{
            'id': slide.id,
            'slide_number': slide.slide_number,
            'content_type': slide.content_type.type_name,
            'content_title': slide.content.title,
            'estimated_time': slide.estimated_time
        } for slide in slides]
    }
    
    return JsonResponse(data)


# 2. courses.py에 뷰 추가
# teacher/courses.py

@login_required
@teacher_required
def course_structure_manage_view(request, course_id):
    """코스 구조 통합 관리 뷰"""
    teacher = request.user.teacher
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # 통계 정보 추가 (선택사항)
    stats = get_course_statistics(course)
    
    context = {
        'course': course,
        'stats': stats,
    }
    
    return render(request, 'teacher/courses/structure_manage.html', context)


@login_required
@teacher_required
def api_contents_search(request):
    """콘텐츠 검색 API"""
    try:
        teacher = request.user.teacher
        
        # 검색 파라미터
        query = request.GET.get('q', '')
        content_type = request.GET.get('content_type', '')
        chapter_id = request.GET.get('chapter', '')
        subchapter_id = request.GET.get('subchapter', '')
        
        # 기본 쿼리셋 - 교사 본인의 콘텐츠 + 공개 콘텐츠
        contents = Contents.objects.filter(
            Q(created_by=request.user) | Q(is_public=True),
            is_active=True
        ).select_related('content_type')
        
        # 검색어 필터
        if query:
            contents = contents.filter(
                Q(title__icontains=query) | 
                Q(page__icontains=query)
            )
        
        # 콘텐츠 타입 필터
        if content_type:
            contents = contents.filter(content_type__type_name=content_type)
        
        # 메타데이터 기반 필터 (chapter, subchapter)
        if chapter_id:
            contents = contents.filter(meta_data__chapter_id=chapter_id)
        
        if subchapter_id:
            contents = contents.filter(meta_data__subchapter_id=subchapter_id)
        
        # 최근 50개만
        contents = contents.order_by('-created_at')[:50]
        
        results = []
        for content in contents:
            results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name,
                'created_at': content.created_at.strftime('%Y.%m.%d'),
                'preview': content.get_preview(100),
                'is_mine': content.created_by == request.user
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
    
# teacher/courses.py 파일의 끝에 다음 두 함수를 추가하세요

@login_required
@teacher_required
def api_course_chapters(request, course_id):
    """특정 코스의 대단원 목록 API"""
    try:
        teacher = request.user.teacher
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        chapters = Chapter.objects.filter(subject=course).order_by('chapter_order')
        
        chapters_data = []
        for chapter in chapters:
            chapters_data.append({
                'id': chapter.id,
                'chapter_name': chapter.chapter_title,  # JavaScript에서 기대하는 필드명
                'title': chapter.chapter_title,  # 다른 코드와 호환성
                'order': chapter.chapter_order
            })
        
        return JsonResponse({
            'success': True,
            'chapters': chapters_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
# teacher/courses.py의 api_chapter_subchapters_list 함수를 다음으로 교체하세요

@login_required
@teacher_required
def api_chapter_subchapters_list(request, chapter_id):
    """특정 대단원의 소단원 목록 API (contents_panel.js용) - 일관성 개선"""
    try:
        teacher = request.user.teacher
        chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=teacher)
        
        subchapters = SubChapter.objects.filter(chapter=chapter).order_by('sub_chapter_order')
        
        subchapters_data = []
        for subchapter in subchapters:
            subchapters_data.append({
                'id': subchapter.id,
                'subchapter_name': subchapter.sub_chapter_title,  # JavaScript에서 기대하는 필드명
                'title': subchapter.sub_chapter_title,  # 다른 코드와 호환성
                'order': subchapter.sub_chapter_order
            })
        
        # 일관성을 위해 객체로 감싸서 반환
        return JsonResponse({
            'success': True,
            'subchapters': subchapters_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)