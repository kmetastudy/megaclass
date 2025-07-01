from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Prefetch, F
from django.utils import timezone
from django.http import JsonResponse
from functools import wraps
from decimal import Decimal

from accounts.models import Student
from teacher.models import (
    Course, CourseAssignment, Chapter, SubChapter, 
    Chasi, ChasiSlide, Contents, ContentType
)
from .models import StudentProgress, StudentAnswer, StudentNote
from datetime import datetime, timedelta




def student_required(view_func):
    """학생 권한 필요한 뷰 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '로그인이 필요합니다.')
            return redirect('accounts:login')
        
        if not hasattr(request.user, 'student'):
            messages.error(request, '학생만 접근 가능합니다.')
            return redirect('accounts:login')
        
        return view_func(request, *args, **kwargs)
    
    return login_required(_wrapped_view)


@login_required
@student_required
def dashboard_view(request):
    """학생 대시보드"""
    student = request.user.student
    
    # 할당받은 코스들
    assigned_courses = CourseAssignment.objects.filter(
        Q(assigned_student=student) | Q(assigned_class=student.school_class)
    ).select_related('course', 'course__teacher')
    
    # 진행 상황
    my_progress = StudentProgress.objects.filter(student=student)
    
    # 전체 슬라이드 수 계산
    course_ids = assigned_courses.values_list('course_id', flat=True).distinct()
    total_slides = ChasiSlide.objects.filter(
        chasi__sub_chapter__chapter__subject__id__in=course_ids
    ).count()  # .count() 추가!
    
    # 완료한 슬라이드 수
    completed_slides = my_progress.filter(is_completed=True).count()
    
    # 진도율 계산
    if total_slides > 0:
        progress_percent = int((completed_slides / total_slides) * 100)
    else:
        progress_percent = 0
    
    # 통계 데이터
    stats = {
        'assigned_courses': assigned_courses.count(),
        'completed_slides': completed_slides,
        'total_slides': total_slides,  # 이제 숫자
        'progress_percent': progress_percent,
        'submitted_answers': StudentAnswer.objects.filter(student=student).count()
    }
    
    # 최근 학습한 슬라이드
    recent_progress = StudentProgress.objects.filter(
        student=student, 
        started_at__isnull=False
    ).select_related(
        'slide__chasi__sub_chapter__chapter__subject',
        'slide__content_type'
    ).order_by('-started_at')[:5]

    # 주간 학습 데이터 계산
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # 월요일
    
    weekly_data = []
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    
    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        
        # 해당 날짜에 완료한 슬라이드 수
        completed_count = StudentProgress.objects.filter(
            student=student,
            completed_at__date=current_date,
            is_completed=True
        ).count()
        
        weekly_data.append({
            'day': day_names[i],
            'count': completed_count,
            'percentage': min(completed_count * 5, 100)  # 20개를 100%로 가정
        })
    
    context = {
        'stats': stats,
        'assigned_courses': assigned_courses[:5],
        'recent_progress': recent_progress,
        'weekly_data': weekly_data,
    }
    
    return render(request, 'student/dashboard.html', context)




@login_required
@student_required
def dashboard_view_0604(request):
    """학생 대시보드"""
    student = request.user.student
    
    # 할당받은 코스들
    # assigned_courses = CourseAssignment.objects.filter(
    #     is_active=True
    # ).filter(
    #     Q(assigned_class=student.school_class) | Q(assigned_student=student)
    # ).select_related('course', 'course__teacher').distinct()
    
    # 옵션 2: 모든 할당된 코스 표시
    assigned_courses = CourseAssignment.objects.filter(
        Q(assigned_student=student) | Q(assigned_class=student.school_class)
    ).select_related('course')

    
    # 진행 상황
    my_progress = StudentProgress.objects.filter(student=student)
    
    # 전체 슬라이드 수 계산
    course_ids = assigned_courses.values_list('course_id', flat=True).distinct()
    total_slides = ChasiSlide.objects.filter(
        chasi__sub_chapter__chapter__subject__id__in=course_ids)
    
    # 완료한 슬라이드 수
    completed_slides = my_progress.filter(is_completed=True).count()
    
    # 진도율 계산
    if total_slides > 0:
        progress_percent = int((completed_slides / total_slides) * 100)
    else:
        progress_percent = 0
    
    # 통계 데이터
    stats = {
        'assigned_courses': assigned_courses.count(),
        'completed_slides': completed_slides,
        'total_slides': total_slides,
        'progress_percent': progress_percent,  # 계산된 진도율 추가
        'submitted_answers': StudentAnswer.objects.filter(student=student).count()
    }
    
    # 최근 학습한 슬라이드
    recent_progress = StudentProgress.objects.filter(
        student=student, 
        started_at__isnull=False
    ).select_related(
        'slide__chasi__sub_chapter__chapter__subject',
        'slide__content_type'
    ).order_by('-started_at')[:5]

    # 주간 학습 데이터 계산
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # 월요일
    
    weekly_data = []
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    
    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        
        # 해당 날짜에 완료한 슬라이드 수
        completed_count = StudentProgress.objects.filter(
            student=student,
            completed_at__date=current_date,
            is_completed=True
        ).count()
        
        weekly_data.append({
            'day': day_names[i],
            'count': completed_count,
            'percentage': min(completed_count * 5, 100)  # 20개를 100%로 가정
        })
    
    
    context = {
        'stats': stats,
        'assigned_courses': assigned_courses[:5],
        'recent_progress': recent_progress,
        'weekly_data': weekly_data,  # 추가
    }
    
    return render(request, 'student/dashboard.html', context)


@login_required
@student_required
def course_list_view(request):
    """내 코스 목록"""
    student = request.user.student
    
    assigned_courses = CourseAssignment.objects.filter(
        Q(assigned_class=student.school_class) | Q(assigned_student=student)
    ).select_related('course', 'course__teacher')
    
    # 각 코스별 진도 계산
    course_data = []
    for assignment in assigned_courses:
        total_slides = ChasiSlide.objects.filter(
            chasi__sub_chapter__chapter__subject=assignment.course,
        ).count()
        
        completed_slides = StudentProgress.objects.filter(
            student=student,
            slide__chasi__sub_chapter__chapter__subject=assignment.course,
            is_completed=True
        ).count()
        
        progress_percent = 0
        if total_slides > 0:
            progress_percent = int((completed_slides / total_slides) * 100)
        
        course_data.append({
            'assignment': assignment,
            'total_slides': total_slides,
            'completed_slides': completed_slides,
            'progress_percent': progress_percent
        })
    
    context = {
        'course_data': course_data,
    }
    
    return render(request, 'student/course_list.html', context)



@login_required
@student_required
def learning_course_view(request, course_id):
    """코스 학습 페이지"""
    try:
        student = request.user.student
        course = get_object_or_404(Course, id=course_id)
        
        # 권한 확인
        has_permission = CourseAssignment.objects.filter(
            course=course,
        ).filter(
            Q(assigned_class=student.school_class) | Q(assigned_student=student)
        ).exists()
        
        if not has_permission:
            messages.error(request, '해당 코스에 접근 권한이 없습니다.')
            return redirect('student:course_list')
        
        # 대단원별로 차시와 슬라이드 가져오기
        chapters = Chapter.objects.filter(
            subject=course
        ).prefetch_related(
            Prefetch('subchapters',
                queryset=SubChapter.objects.filter(
                    subject=course
                ).prefetch_related(
                    Prefetch('chasis',
                        queryset=Chasi.objects.filter(
                            subject=course,
                            is_published=True
                        ).prefetch_related(
                            Prefetch('teacher_slides',
                                queryset=ChasiSlide.objects.filter(

                                ).select_related('content_type', 'content')
                            )
                        )
                    )
                )
            )
        ).order_by('chapter_order')
        
        # 진도 정보를 딕셔너리로 변환
        progress_list = StudentProgress.objects.filter(
            student=student,
            slide__chasi__sub_chapter__chapter__subject=course
        ).select_related('slide')
        
        # 진도 정보를 처리하여 템플릿에서 사용하기 쉽게 만들기
        progress_data = {}
        for progress in progress_list:
            progress_data[progress.slide.id] = {
                'is_completed': progress.is_completed,
                'started_at': progress.started_at,
                'view_count': progress.view_count
            }
        
        # 전체 진도율 계산
        total_slides = ChasiSlide.objects.filter(
            chasi__sub_chapter__chapter__subject=course
        ).count()
        
        completed_slides = progress_list.filter(is_completed=True).count()
        
        if total_slides > 0:
            overall_progress = int((completed_slides / total_slides) * 100)
        else:
            overall_progress = 0
        
        context = {
            'course': course,
            'chapters': chapters,
            'progress_data': progress_data,
            'overall_progress': overall_progress,
            'total_slides': total_slides,
            'completed_slides': completed_slides,
        }
        
        return render(request, 'student/learning_course.html', context)
        
    except Exception as e:
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
        return redirect('student:course_list')


@login_required
@student_required
def slide_view(request, slide_id):
    """슬라이드 학습 페이지"""
    try:
        student = request.user.student
        
        # 슬라이드 조회
        slide = get_object_or_404(
            ChasiSlide.objects.select_related(
                'chasi__sub_chapter__chapter__subject',
                'content',
                'content_type'
            ),
            id=slide_id
        )
        
        # 코스 가져오기
        course = slide.chasi.sub_chapter.chapter.subject
        
        # 권한 확인
        has_access = CourseAssignment.objects.filter(
            course=course
        ).filter(
            Q(assigned_class=student.school_class) | Q(assigned_student=student)
        ).exists()
        
        if not has_access:
            messages.error(request, '해당 슬라이드에 접근 권한이 없습니다.')
            return redirect('student:course_list')
        
        # 진도 체크 및 생성
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            slide=slide,
            defaults={'view_count': 0}  # 기본값 설정
        )
        
        # 처음 시작하는 경우
        if not progress.started_at:
            progress.started_at = timezone.now()
        
        # 조회수 증가
        progress.view_count += 1
        progress.save()
        
        # 기존 답안 확인 - 가장 최근 답안
        existing_answer = StudentAnswer.objects.filter(
            student=student,
            slide=slide
        ).order_by('-submitted_at').first()
        
        # 노트 가져오기
        note = StudentNote.objects.filter(
            student=student,
            slide=slide
        ).first()
        
        # 답안 제출 처리
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'submit_answer' and slide.content.answer:
                answer = request.POST.get('answer', '').strip()
                
                if answer:
                    # 새로운 답안 생성 (여러 번 제출 가능)
                    student_answer = StudentAnswer.objects.create(
                        student=student,
                        slide=slide,
                        answer=answer
                    )
                    
                    # 자동 채점 (단답형/객관식)
                    correct_answer = slide.content.answer.strip()
                    
                    if slide.content_type.type_name in ['단답형', '객관식']:
                        is_correct = answer == correct_answer
                        student_answer.is_correct = is_correct
                        student_answer.score = 100.0 if is_correct else 0.0
                        student_answer.save()
                        
                        if is_correct:
                            messages.success(request, '정답입니다! 잘했어요!')
                        else:
                            messages.error(request, f'오답입니다. 정답은 "{correct_answer}"입니다.')
                    else:
                        # 서술형은 수동 채점 필요
                        messages.success(request, '답안이 제출되었습니다. 선생님이 확인 후 점수를 매길 예정입니다.')
                    
                    # 문제가 있는 슬라이드를 완료 처리
                    if not progress.is_completed:
                        progress.is_completed = True
                        progress.completed_at = timezone.now()
                        progress.save()
                    
                    # 답안 제출 후 existing_answer 업데이트
                    existing_answer = student_answer
                else:
                    messages.error(request, '답안을 입력해주세요.')
            
            elif action == 'complete':
                # 진도 완료 처리 (문제가 없는 슬라이드)
                if not progress.is_completed:
                    progress.is_completed = True
                    progress.completed_at = timezone.now()
                    progress.save()
                    messages.success(request, '학습을 완료했습니다.')
            
            # POST 처리 후 같은 페이지 유지 (PRG 패턴)
            if action in ['submit_answer', 'complete'] and not messages.get_messages(request):
                # 다음 슬라이드로 자동 이동하려면 아래 주석 해제
                # next_slide = ChasiSlide.objects.filter(
                #     chasi=slide.chasi,
                #     slide_number__gt=slide.slide_number
                # ).first()
                # 
                # if next_slide:
                #     return redirect('student:slide_view', slide_id=next_slide.id)
                pass
        
        # 이전/다음 슬라이드
        prev_slide = ChasiSlide.objects.filter(
            chasi=slide.chasi,
            slide_number__lt=slide.slide_number
        ).order_by('-slide_number').first()
        
        next_slide = ChasiSlide.objects.filter(
            chasi=slide.chasi,
            slide_number__gt=slide.slide_number
        ).order_by('slide_number').first()
        
        # 현재 슬라이드 위치
        total_slides_in_chasi = slide.chasi.teacher_slides.count()
        
        # 객관식 옵션 처리 - content의 meta_data 필드 확인
        options = []
        if slide.content_type.type_name == '객관식':
            # content.meta_data가 딕셔너리인지 확인
            if hasattr(slide.content, 'meta_data') and isinstance(slide.content.meta_data, dict):
                options = slide.content.meta_data.get('options', [])
            # 또는 content.page에서 옵션 추출 (필요시)
        
        context = {
            'slide': slide,
            'progress': progress,
            'existing_answer': existing_answer,
            'note': note,
            'prev_slide': prev_slide,
            'next_slide': next_slide,
            'total_slides_in_chasi': total_slides_in_chasi,
            'options': options,
            'course': course,  # 추가
        }
        
        return render(request, 'student/slide_view.html', context)
        
    except Exception as e:
        import traceback
        print(f"Error in slide_view: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
        return redirect('student:course_list')

@login_required
@student_required
def slide_view_0603(request, slide_id):
    """슬라이드 학습 페이지"""
    try:
        student = request.user.student
        
        # 슬라이드 조회
        slide = get_object_or_404(
            ChasiSlide.objects.select_related(
                'chasi__sub_chapter__chapter__subject',
                'content',
                'content_type'
            ),
            id=slide_id
        )
        
        # 코스 가져오기
        course = slide.chasi.subject  # 또는 slide.chasi.sub_chapter.chapter.subject
        
        # 권한 확인
        has_access = CourseAssignment.objects.filter(
            course=course
        ).filter(
            Q(assigned_class=student.school_class) | Q(assigned_student=student)
        ).exists()
        
        if not has_access:
            messages.error(request, '해당 슬라이드에 접근 권한이 없습니다.')
            return redirect('student:course_list')
        
        # 진도 체크 및 생성
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            slide=slide
        )
        
        # 처음 시작하는 경우
        if not progress.started_at:
            progress.started_at = timezone.now()
        
        # 조회수 증가
        progress.view_count = F('view_count') + 1
        progress.save(update_fields=['started_at', 'view_count'])
        
        # 기존 답안 확인
        existing_answer = StudentAnswer.objects.filter(
            student=student,
            slide=slide
        ).order_by('-submitted_at').first()
        
        # 노트 가져오기
        note = StudentNote.objects.filter(
            student=student,
            slide=slide
        ).first()
        
        # 답안 제출 처리
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'submit_answer':
                answer = request.POST.get('answer')
                if answer and slide.content.answer:
                    student_answer = StudentAnswer.objects.create(
                        student=student,
                        slide=slide,
                        answer=answer
                    )
                    
                    # 자동 채점 (단답형인 경우)
                    if slide.content_type.type_name in ['단답형', '객관식']:
                        is_correct = answer.strip() == slide.content.answer.strip()
                        student_answer.is_correct = is_correct
                        student_answer.score = Decimal('100') if is_correct else Decimal('0')
                        student_answer.save(update_fields=['is_correct', 'score'])
                    
                    messages.success(request, '답안이 제출되었습니다.')
            
            elif action == 'complete':
                # 진도 완료 처리
                progress.is_completed = True
                progress.completed_at = timezone.now()
                progress.save(update_fields=['is_completed', 'completed_at'])
                messages.success(request, '학습을 완료했습니다.')
            
            # 다음 슬라이드로 이동
            if action in ['submit_answer', 'complete']:
                next_slide = ChasiSlide.objects.filter(
                    chasi=slide.chasi,
                    slide_number__gt=slide.slide_number
                ).first()
                
                if next_slide:
                    return redirect('student:slide_view', slide_id=next_slide.id)
                else:
                    messages.info(request, '이 차시의 학습을 완료했습니다.')
                    return redirect('student:learning_course', course_id=course.id)
        
        # 이전/다음 슬라이드
        prev_slide = ChasiSlide.objects.filter(
            chasi=slide.chasi,
            slide_number__lt=slide.slide_number
        ).order_by('-slide_number').first()
        
        next_slide = ChasiSlide.objects.filter(
            chasi=slide.chasi,
            slide_number__gt=slide.slide_number
        ).order_by('slide_number').first()
        
        # progress 재조회 (F 객체 사용 후)
        progress.refresh_from_db()
        
        # 현재 슬라이드 위치
        total_slides_in_chasi = slide.chasi.teacher_slides.all().count()
        
        # 객관식 옵션 처리
        options = []
        if slide.content_type.type_name == '객관식' and hasattr(slide.content, 'meta_data'):
            if isinstance(slide.content.meta_data, dict) and 'options' in slide.content.meta_data:
                options = slide.content.meta_data['options']
        
        context = {
            'slide': slide,
            'progress': progress,
            'existing_answer': existing_answer,
            'note': note,
            'prev_slide': prev_slide,
            'next_slide': next_slide,
            'total_slides_in_chasi': total_slides_in_chasi,
            'options': options,
        }
        
        return render(request, 'student/slide_view.html', context)
        
    except Exception as e:
        import traceback
        print(f"Error in slide_view: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, '오류가 발생했습니다.')
        return redirect('student:course_list')

@login_required
@student_required
def progress_view(request):
    """학습 진도 현황"""
    student = request.user.student
    
    # 코스별 진도
    assigned_courses = CourseAssignment.objects.filter(
        Q(assigned_class=student.school_class) | Q(assigned_student=student)
    ).select_related('course')
    
    course_progress = []
    for assignment in assigned_courses:
        course = assignment.course
        
        # 전체 슬라이드 수
        total_slides = ChasiSlide.objects.filter(
            chasi__sub_chapter__chapter__subject=course
        ).count()
        
        # 완료한 슬라이드 수
        completed_slides = StudentProgress.objects.filter(
            student=student,
            slide__chasi__sub_chapter__chapter__subject=course,
            is_completed=True
        ).count()
        
        # 평균 점수
        avg_score_result = StudentAnswer.objects.filter(
            student=student,
            slide__chasi__sub_chapter__chapter__subject=course,
            score__isnull=False
        ).aggregate(avg=Avg('score'))
        
        avg_score = avg_score_result['avg'] if avg_score_result['avg'] else 0
        
        # 진도율 계산
        progress_percent = 0
        if total_slides > 0:
            progress_percent = int((completed_slides / total_slides) * 100)
        
        # 진행 중인 슬라이드 수
        in_progress = StudentProgress.objects.filter(
            student=student,
            slide__chasi__sub_chapter__chapter__subject=course,
            is_completed=False,
            started_at__isnull=False
        ).count()
        
        # 미시작 슬라이드 수
        not_started = total_slides - completed_slides - in_progress
        
        course_progress.append({
            'course': course,
            'total_slides': total_slides,
            'completed_slides': completed_slides,
            'in_progress': in_progress,
            'not_started': not_started,
            'progress_percent': progress_percent,
            'avg_score': round(float(avg_score), 1) if avg_score else 0,
        })
    
    # 최근 학습 기록
    recent_activities = StudentProgress.objects.filter(
        student=student
    ).select_related(
        'slide__chasi__sub_chapter__chapter__subject',
        'slide__content_type'
    ).order_by('-started_at')[:20]
    
    # 학습 통계
    total_study_time = StudentProgress.objects.filter(
        student=student,
        completed_at__isnull=False
    ).count()  # 실제로는 시간 계산 로직 필요
    
    context = {
        'course_progress': course_progress,
        'recent_activities': recent_activities,
        'total_study_time': total_study_time,
    }
    
    return render(request, 'student/progress.html', context)


@login_required
@student_required
def my_answers_view(request):
    """내 답안 목록"""
    student = request.user.student
    
    # 기본 쿼리
    answers = StudentAnswer.objects.filter(
        student=student
    ).select_related(
        'slide__chasi__sub_chapter__chapter__subject',
        'slide__content_type'
    ).order_by('-submitted_at')
    
    # 필터링
    course_id = request.GET.get('course')
    if course_id:
        answers = answers.filter(slide__chasi__sub_chapter__chapter__subject_id=course_id)
    
    # 정답 여부 필터
    correct_filter = request.GET.get('correct')
    if correct_filter == 'true':
        answers = answers.filter(is_correct=True)
    elif correct_filter == 'false':
        answers = answers.filter(is_correct=False)
    
    # 통계 계산
    total_answers = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    incorrect_answers = answers.filter(is_correct=False).count()
    
    # 코스 목록 - courseassignment를 assignments로 변경
    courses = Course.objects.filter(
        assignments__in=CourseAssignment.objects.filter(
            Q(assigned_class=student.school_class) | Q(assigned_student=student)
        )
    ).distinct()
    
    context = {
        'answers': answers,
        'courses': courses,
        'total_answers': total_answers,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
    }
    
    return render(request, 'student/my_answers.html', context)

@login_required
@student_required
def my_answers_view_0603(request):
    """내 답안 목록"""
    student = request.user.student
    
    # 기본 쿼리
    answers = StudentAnswer.objects.filter(
        student=student
    ).select_related(
        'slide__chasi__sub_chapter__chapter__subject',
        'slide__content_type'
    ).order_by('-submitted_at')
    
    # 필터링
    course_id = request.GET.get('course')
    if course_id:
        answers = answers.filter(slide__chasi__sub_chapter__chapter__subject_id=course_id)
    
    # 정답 여부 필터
    correct_filter = request.GET.get('correct')
    if correct_filter == 'true':
        answers = answers.filter(is_correct=True)
    elif correct_filter == 'false':
        answers = answers.filter(is_correct=False)
    
    # 통계 계산
    total_answers = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    incorrect_answers = answers.filter(is_correct=False).count()
    
    # 코스 목록
    courses = Course.objects.filter(
        courseassignment__in=CourseAssignment.objects.filter(
            Q(assigned_class=student.school_class) | Q(assigned_student=student)
        )
    ).distinct()
    
    context = {
        'answers': answers,
        'courses': courses,
        'total_answers': total_answers,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
    }
    
    return render(request, 'student/my_answers.html', context)


@login_required
@student_required
def save_note_ajax(request, slide_id):
    """노트 저장 AJAX 처리"""
    if request.method == 'POST':
        student = request.user.student
        slide = get_object_or_404(ChasiSlide, id=slide_id)
        
        note_content = request.POST.get('note_content', '')
        
        if note_content.strip():
            note, created = StudentNote.objects.update_or_create(
                student=student,
                slide=slide,
                defaults={'content': note_content}
            )
            return JsonResponse({'status': 'success'})
        else:
            # 빈 내용이면 노트 삭제
            StudentNote.objects.filter(student=student, slide=slide).delete()
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'})

@login_required
@student_required
def course_progress_api(request, course_id):
    """코스 진도 API"""
    student = request.user.student
    course = get_object_or_404(Course, id=course_id)
    
    # 전체 슬라이드 수
    total_slides = ChasiSlide.objects.filter(
        chasi__sub_chapter__chapter__subject=course
    ).count()
    
    # 완료한 슬라이드 수
    completed_slides = StudentProgress.objects.filter(
        student=student,
        slide__chasi__sub_chapter__chapter__subject=course,
        is_completed=True
    ).count()
    
    progress_percent = 0
    if total_slides > 0:
        progress_percent = int((completed_slides / total_slides) * 100)
    
    return JsonResponse({
        'total_slides': total_slides,
        'completed_slides': completed_slides,
        'progress_percent': progress_percent,
    })


