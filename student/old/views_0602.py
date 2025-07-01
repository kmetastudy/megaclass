from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from accounts.models import Student
from teacher.models import Course, CourseAssignment
from teacher.models import Chasi, ChasiSlide
from .models import StudentProgress, StudentAnswer
import json

def student_required(view_func):
    """학생 권한 필요한 뷰 데코레이터"""
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'student'):
            messages.error(request, '학생만 접근 가능합니다.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@student_required
def dashboard_view(request):
    """학생 대시보드"""
    student = request.user.student
    
    # 할당받은 코스들
    assigned_courses = CourseAssignment.objects.filter(
        Q(assigned_class=student.school_class) | Q(assigned_student=student)
    )
    
    # 진행 상황
    my_progress = StudentProgress.objects.filter(student=student)
    
    # 통계 데이터
    stats = {
        'assigned_courses': assigned_courses.count(),
        'completed_slides': my_progress.filter(is_completed=True).count(),
        'total_slides': my_progress.count(),
        'submitted_answers': StudentAnswer.objects.filter(student=student).count()
    }
    
    # 최근 학습한 코스들
    recent_progress = StudentProgress.objects.filter(
        student=student, 
        started_at__isnull=False
    ).order_by('-started_at')[:5]
    
    context = {
        'stats': stats,
        'assigned_courses': assigned_courses[:5],
        'recent_progress': recent_progress,
    }
    
    return render(request, 'student/dashboard.html', context)

@login_required
@student_required
def course_list_view(request):
    """내 코스 목록"""
    student = request.user.student
    
    # 할당받은 코스들
    assigned_courses = CourseAssignment.objects.filter(
        Q(assigned_class=student.school_class) | Q(assigned_student=student)
    ).select_related('course', 'course__teacher__user')
    
    # 각 코스의 진행률 계산
    courses_with_progress = []
    for assignment in assigned_courses:
        course = assignment.course
        total_slides = ChasiSlide.objects.filter(chasi__subject=course).count()
        completed_slides = StudentProgress.objects.filter(
            student=student,
            slide__chasi__subject=course,
            is_completed=True
        ).count()
        
        progress_percent = (completed_slides / total_slides * 100) if total_slides > 0 else 0
        
        courses_with_progress.append({
            'assignment': assignment,
            'course': course,
            'total_slides': total_slides,
            'completed_slides': completed_slides,
            'progress_percent': round(progress_percent, 1)
        })
    
    context = {
        'courses_with_progress': courses_with_progress,
    }
    
    return render(request, 'student/courses/list.html', context)

@login_required
@student_required
def learning_course_view(request, course_id):
    """코스 학습 페이지"""
    student = request.user.student
    
    # 코스 접근 권한 확인
    has_access = CourseAssignment.objects.filter(
        Q(assigned_class=student.school_class) | Q(assigned_student=student), # Q 객체를 앞으로 이동
        course=slide.chasi.subject
    ).exists()
    if not has_access:
        messages.error(request, '해당 코스에 접근할 권한이 없습니다.')
        return redirect('student:course_list')
    
    # 코스의 차시들
    chasis = Chasi.objects.filter(subject=course).order_by('chasi_order')
    
    # 각 차시의 진행 상황
    chasis_with_progress = []
    for chasi in chasis:
        slides = ChasiSlide.objects.filter(chasi=chasi).order_by('slide_number')
        total_slides = slides.count()
        completed_slides = StudentProgress.objects.filter(
            student=student,
            slide__in=slides,
            is_completed=True
        ).count()
        
        progress_percent = (completed_slides / total_slides * 100) if total_slides > 0 else 0
        
        chasis_with_progress.append({
            'chasi': chasi,
            'total_slides': total_slides,
            'completed_slides': completed_slides,
            'progress_percent': round(progress_percent, 1),
            'slides': slides
        })
    
    context = {
        'course': course,
        'chasis_with_progress': chasis_with_progress,
    }
    
    return render(request, 'student/learning/course_view.html', context)

@login_required
@student_required
def learning_slide_view(request, slide_id):
    """슬라이드 학습 페이지"""
    student = request.user.student
    slide = get_object_or_404(ChasiSlide, id=slide_id)
    
    # 코스 접근 권한 확인
    has_access = CourseAssignment.objects.filter(
        Q(assigned_class=student.school_class) | Q(assigned_student=student), # Q 객체를 앞으로 이동
        course=slide.chasi.subject
    ).exists()
    
    if not has_access:
        messages.error(request, '해당 코스에 접근할 권한이 없습니다.')
        return redirect('student:course_list')
    
    # 진행 상황 생성 또는 업데이트
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        slide=slide,
        defaults={'started_at': timezone.now()}
    )
    
    if created or not progress.started_at:
        progress.started_at = timezone.now()
        progress.save()
    
    # 기존 답안 확인
    existing_answer = StudentAnswer.objects.filter(
        student=student,
        slide=slide
    ).first()
    
    # 답안 제출 처리
    if request.method == 'POST':
        answer_data = {
            'type': slide.content_type.type_name,
            'answer': request.POST.get('answer', ''),
            'submitted_at': timezone.now().isoformat()
        }
        
        StudentAnswer.objects.update_or_create(
            student=student,
            slide=slide,
            defaults={
                'answer_data': answer_data,
                'submitted_at': timezone.now()
            }
        )
        
        # 진행 상황 완료 처리
        progress.completed_at = timezone.now()
        progress.is_completed = True
        progress.save()
        
        messages.success(request, '답안이 제출되었습니다.')
        
        # 다음 슬라이드로 이동
        next_slide = ChasiSlide.objects.filter(
            chasi=slide.chasi,
            slide_number__gt=slide.slide_number
        ).order_by('slide_number').first()
        
        if next_slide:
            return redirect('student:learning_slide', slide_id=next_slide.id)
        else:
            return redirect('student:learning_course', course_id=slide.chasi.subject.id)
    
    # 코스 내 다른 슬라이드들
    course_slides = ChasiSlide.objects.filter(
        chasi__subject=slide.chasi.subject
    ).order_by('chasi__chasi_order', 'slide_number')
    
    context = {
        'slide': slide,
        'course': slide.chasi.subject,
        'chasi': slide.chasi,
        'progress': progress,
        'existing_answer': existing_answer,
        'course_slides': course_slides,
    }
    
    return render(request, 'student/learning/slide_view.html', context)

@login_required
@student_required
def progress_view(request):
    """학습 진도 확인"""
    student = request.user.student
    
    # 할당받은 코스들의 진행 상황
    assigned_courses = CourseAssignment.objects.filter(
        Q(assigned_class=student.school_class) | Q(assigned_student=student)
    )
    
    courses_progress = []
    total_completed = 0
    total_slides = 0
    
    for assignment in assigned_courses:
        course = assignment.course
        chasis = Chasi.objects.filter(subject=course).order_by('chasi_order')
        
        course_total_slides = 0
        course_completed_slides = 0
        chasis_progress = []
        
        for chasi in chasis:
            slides = ChasiSlide.objects.filter(chasi=chasi)
            chasi_total = slides.count()
            chasi_completed = StudentProgress.objects.filter(
                student=student,
                slide__in=slides,
                is_completed=True
            ).count()
            
            chasi_progress.append({
                'chasi': chasi,
                'total_slides': chasi_total,
                'completed_slides': chasi_completed,
                'progress_percent': (chasi_completed / chasi_total * 100) if chasi_total > 0 else 0
            })
            
            course_total_slides += chasi_total
            course_completed_slides += chasi_completed
        
        course_progress_percent = (course_completed_slides / course_total_slides * 100) if course_total_slides > 0 else 0
        
        courses_progress.append({
            'course': course,
            'total_slides': course_total_slides,
            'completed_slides': course_completed_slides,
            'progress_percent': round(course_progress_percent, 1),
            'chasis_progress': chasis_progress
        })
        
        total_completed += course_completed_slides
        total_slides += course_total_slides
    
    # 전체 진행률
    overall_progress = (total_completed / total_slides * 100) if total_slides > 0 else 0
    
    # 최근 학습 통계
    recent_answers = StudentAnswer.objects.filter(student=student).order_by('-submitted_at')[:10]
    
    context = {
        'courses_progress': courses_progress,
        'overall_progress': round(overall_progress, 1),
        'total_completed': total_completed,
        'total_slides': total_slides,
        'recent_answers': recent_answers,
    }
    
    return render(request, 'student/progress/index.html', context)