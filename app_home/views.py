# views.py (수정된 버전)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from django.db.models import Sum, Count, Q, Avg, F
import json
from datetime import datetime

from app_home.models import (
    HealthHabitTracker, DailyReflection, 
    DailyReflectionEvaluation, TrackerEvaluation
)
from accounts.models import Student, Teacher, Class
from teacher.models import ChasiSlide

# 학생용 뷰
@login_required
def student_health_habit_view(request, slide_id):
    """학생용 건강 습관 기록 페이지"""
    if not hasattr(request.user, 'student'):
        return JsonResponse({'error': '학생만 접근 가능합니다.'}, status=403)
    
    # 6가지 고정된 약속
    default_promises = {
        1: '바른 자세로 생활하기',
        2: '규칙적으로 가벼운 운동하기',
        3: '바른 식습관 기르기',
        4: '몸을 깨끗하게 하기',
        5: '생활 주변을 깨끗하게 하기',
        6: '마음 건강하게 관리하기'
    }
    
    # 약속 데이터 준비 - title 필드 추가
    promises_list = []
    for i in range(1, 7):
        promises_list.append({
            'number': i,
            'title': default_promises[i],  # title 필드 추가
            'placeholder': f'약속 {i}을 적어보세요!'
        })
    
    # 요일 데이터 준비
    week_days = [
        {'num': 1, 'name': '월'},
        {'num': 2, 'name': '화'},
        {'num': 3, 'name': '수'},
        {'num': 4, 'name': '목'},
        {'num': 5, 'name': '금'},
        {'num': 6, 'name': '토'},
        {'num': 7, 'name': '일'},
    ]
    
    context = {
        'slide_id': slide_id,
        'user': request.user,
        'promises_list': promises_list,
        'week_days': week_days,
    }
    return render(request, 'health_habit/student_health_habit.html', context)


@login_required
def get_tracker_data(request, slide_id):
    """트래커 데이터 조회"""
    try:
        student = request.user.student
        
        # 6가지 고정된 약속
        default_promises = {
            '1': '바른 자세로 생활하기',
            '2': '규칙적으로 가벼운 운동하기',
            '3': '바른 식습관 기르기',
            '4': '몸을 깨끗하게 하기',
            '5': '생활 주변을 깨끗하게 하기',
            '6': '마음 건강하게 관리하기'
        }
        
        tracker, created = HealthHabitTracker.objects.get_or_create(
            student=student,
            slide_id=slide_id,
            defaults={'promises': default_promises}
        )
        
        # 기존 트래커에 약속이 없으면 추가
        if not tracker.promises:
            tracker.promises = default_promises
            tracker.save()
        
        # 리플렉션 데이터 포함
        reflections = []
        total_stars = 0
        
        for reflection in tracker.reflections.select_related('evaluation'):
            ref_data = {
                'promise_number': reflection.promise_number,
                'week': reflection.week,
                'day': reflection.day,
                'has_evaluation': hasattr(reflection, 'evaluation')
            }
            
            if hasattr(reflection, 'evaluation'):
                total_stars += reflection.evaluation.score
            
            reflections.append(ref_data)
        
        # 통계 계산
        stats = tracker.get_completion_stats()
        stats['total_stars'] = total_stars
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': tracker.id,
                'promises': tracker.promises,
                'reflections': reflections,
                'statistics': stats,
                'is_submitted': tracker.is_submitted
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@login_required
def save_promises(request):
    """약속 저장"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student = request.user.student
            slide_id = data.get('slide_id')
            promises = data.get('promises')
            
            tracker, _ = HealthHabitTracker.objects.get_or_create(
                student=student,
                slide_id=slide_id
            )
            
            tracker.promises = promises
            tracker.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_promise_statistics(request, slide_id):
    """약속별 통계 데이터 조회"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    class_id = request.GET.get('class_id')
    
    # 교사가 담당하는 학급의 학생들만 조회
    teacher_classes = teacher.classes.all()
    
    # 트래커 조회
    trackers_query = HealthHabitTracker.objects.filter(
        slide_id=slide_id,
        student__school_class__in=teacher_classes
    )
    
    if class_id:
        trackers_query = trackers_query.filter(student__school_class_id=class_id)
    
    # 각 약속별 통계 계산
    promise_stats = []
    promise_names = {
        1: '바른자세',
        2: '운동',
        3: '식습관',
        4: '위생',
        5: '정리',
        6: '마음건강'
    }
    
    for promise_num in range(1, 7):
        # 해당 약속에 대한 모든 리플렉션 수 계산
        total_reflections = DailyReflection.objects.filter(
            tracker__in=trackers_query,
            promise_number=promise_num
        ).count()
        
        # 전체 가능한 리플렉션 수 (학생수 * 14일)
        total_possible = trackers_query.count() * 14
        
        # 완료율 계산
        completion_rate = (total_reflections / total_possible * 100) if total_possible > 0 else 0
        
        promise_stats.append({
            'promise_num': promise_num,
            'name': promise_names[promise_num],
            'total_reflections': total_reflections,
            'total_possible': total_possible,
            'completion_rate': round(completion_rate, 1)
        })
    
    # 주차별 통계
    week_stats = []
    for week in [1, 2]:
        week_reflections = DailyReflection.objects.filter(
            tracker__in=trackers_query,
            week=week
        ).count()
        
        week_possible = trackers_query.count() * 6 * 7  # 학생수 * 6개약속 * 7일
        week_rate = (week_reflections / week_possible * 100) if week_possible > 0 else 0
        
        week_stats.append({
            'week': week,
            'reflections': week_reflections,
            'rate': round(week_rate, 1)
        })
    
    # 평가 통계
    evaluation_stats = {
        'total_evaluations': DailyReflectionEvaluation.objects.filter(
            reflection__tracker__in=trackers_query
        ).count(),
        'score_distribution': DailyReflectionEvaluation.objects.filter(
            reflection__tracker__in=trackers_query
        ).values('score').annotate(count=Count('score')).order_by('score')
    }
    
    return JsonResponse({
        'success': True,
        'promise_stats': promise_stats,
        'week_stats': week_stats,
        'evaluation_stats': {
            'total_evaluations': evaluation_stats['total_evaluations'],
            'score_distribution': list(evaluation_stats['score_distribution'])
        }
    })


@csrf_exempt
@login_required
def save_reflection(request):
    """일일 소감 저장"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tracker_id = data.get('tracker_id')
            
            tracker = get_object_or_404(HealthHabitTracker, id=tracker_id)
            
            # 권한 확인
            if tracker.student != request.user.student:
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
            
            # 날짜 문자열을 date 객체로 변환
            reflection_date = data.get('reflection_date')
            if isinstance(reflection_date, str):
                reflection_date = datetime.strptime(reflection_date, '%Y-%m-%d').date()
            
            # DailyReflection 생성 또는 업데이트
            reflection, created = DailyReflection.objects.update_or_create(
                tracker=tracker,
                promise_number=data.get('promise_number'),
                week=data.get('week'),
                day=data.get('day'),
                defaults={
                    'reflection_text': data.get('reflection_text'),
                    'reflection_date': reflection_date,
                    'reflection_time': data.get('reflection_time')
                }
            )
            
            return JsonResponse({
                'success': True,
                'created': created,
                'reflection_id': reflection.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_reflection(request, tracker_id, promise, week, day):
    """특정 소감 조회"""
    try:
        tracker = get_object_or_404(HealthHabitTracker, id=tracker_id)
        
        # 권한 확인
        if tracker.student != request.user.student:
            return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        reflection = DailyReflection.objects.filter(
            tracker=tracker,
            promise_number=promise,
            week=week,
            day=day
        ).first()
        
        if reflection:
            return JsonResponse({
                'success': True,
                'data': {
                    'reflection_text': reflection.reflection_text,
                    'reflection_date': str(reflection.reflection_date),
                    'reflection_time': str(reflection.reflection_time)
                }
            })
        else:
            return JsonResponse({'success': True, 'data': None})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_promise_reflections(request, tracker_id, promise_num):
    """약속별 소감 목록"""
    try:
        tracker = get_object_or_404(HealthHabitTracker, id=tracker_id)
        
        # 권한 확인
        if tracker.student != request.user.student:
            return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        reflections = DailyReflection.objects.filter(
            tracker=tracker,
            promise_number=promise_num
        ).select_related('evaluation').order_by('week', 'day')
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        
        data = []
        for ref in reflections:
            ref_data = {
                'id': ref.id,
                'week': ref.week,
                'day': ref.day,
                'day_name': days[ref.day - 1],
                'reflection_text': ref.reflection_text,
                'reflection_date': str(ref.reflection_date)
            }
            
            # 평가 정보 추가
            if hasattr(ref, 'evaluation'):
                ref_data['evaluation'] = {
                    'score': ref.evaluation.score,
                    'emoji': ref.evaluation.get_emoji_feedback_display(),
                    'comment': ref.evaluation.comment
                }
            
            data.append(ref_data)
        
        return JsonResponse({
            'success': True,
            'reflections': data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_final_reflection(request, tracker_id):
    """최종 소감 조회"""
    try:
        tracker = get_object_or_404(HealthHabitTracker, id=tracker_id)
        
        # 권한 확인
        is_teacher = hasattr(request.user, 'teacher')
        is_owner = hasattr(request.user, 'student') and tracker.student == request.user.student
        
        if not (is_teacher or is_owner):
            return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        return JsonResponse({
            'success': True,
            'data': tracker.final_reflection
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@login_required
def submit_final(request):
    """최종 제출"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tracker_id = data.get('tracker_id')
            final_reflection = data.get('final_reflection')
            
            tracker = get_object_or_404(HealthHabitTracker, id=tracker_id)
            
            # 권한 확인
            if tracker.student != request.user.student:
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
            
            tracker.final_reflection = final_reflection
            tracker.is_submitted = True
            tracker.submitted_at = timezone.now()
            tracker.save()
            
            return JsonResponse({
                'success': True,
                'message': '제출이 완료되었습니다!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# 교사용 뷰
@login_required
def teacher_evaluation_view(request, slide_id):
    """교사용 평가 페이지"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    
    # 교사가 담당하는 학급 목록
    classes = teacher.classes.all()
    
    # 요일 데이터 준비
    week_days = [
        {'num': 1, 'name': '월'},
        {'num': 2, 'name': '화'},
        {'num': 3, 'name': '수'},
        {'num': 4, 'name': '목'},
        {'num': 5, 'name': '금'},
        {'num': 6, 'name': '토'},
        {'num': 7, 'name': '일'},
    ]
    
    context = {
        'slide_id': slide_id,  # slide_id를 context에 추가
        'classes': classes,
        'user': request.user,
        'week_days': week_days,
    }
    return render(request, 'health_habit/teacher_evaluation.html', context)


@login_required
def get_students_for_evaluation(request, slide_id):
    """평가를 위한 학생 목록"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    class_id = request.GET.get('class_id')
    
    # 교사가 담당하는 학급의 학생들만 조회
    teacher_classes = teacher.classes.all()
    
    # 쿼리 작성 - 제출 여부와 관계없이 모든 트래커 조회
    trackers = HealthHabitTracker.objects.filter(
        slide_id=slide_id,
        student__school_class__in=teacher_classes
    ).select_related(
        'student__user', 
        'student__school_class',
        'overall_evaluation'
    ).prefetch_related(
        'reflections__evaluation'
    )
    
    if class_id:
        trackers = trackers.filter(student__school_class_id=class_id)
    
    students = []
    for tracker in trackers:
        stats = tracker.get_completion_stats()
        
        # 받은 별 개수 계산
        total_stars = tracker.reflections.filter(
            evaluation__isnull=False
        ).aggregate(
            total=Sum('evaluation__score')
        )['total'] or 0
        
        # 평가 여부
        is_evaluated = hasattr(tracker, 'overall_evaluation')
        
        # 학번에서 번호 추출
        student_number = tracker.student.student_id.split('_')[-1] if '_' in tracker.student.student_id else tracker.student.student_id
        
        students.append({
            'tracker_id': tracker.id,
            'name': tracker.student.user.get_full_name(),
            'student_grade': tracker.student.school_class.grade,
            'class_number': tracker.student.school_class.class_number,
            'number': student_number,
            'completion_rate': stats['completion_rate'],
            'total_reflections': stats['total_reflections'],
            'total_stars': total_stars,
            'is_evaluated': is_evaluated,
            'is_submitted': tracker.is_submitted,
            'evaluation_grade': tracker.overall_evaluation.grade if is_evaluated else None
        })
    
    # 이름순으로 정렬
    students.sort(key=lambda x: x['name'])
    
    return JsonResponse({
        'success': True,
        'students': students
    })


@login_required
def get_student_detail_for_evaluation(request, tracker_id):
    """학생 상세 정보"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    tracker = get_object_or_404(HealthHabitTracker, id=tracker_id)
    
    # 교사 권한 확인 - 해당 학생의 학급을 담당하는지 확인
    if tracker.student.school_class not in teacher.classes.all():
        return JsonResponse({'error': '해당 학생을 평가할 권한이 없습니다.'}, status=403)
    
    # 약속별 소감 정리
    promises = []
    
    # 6가지 고정된 약속
    default_promises = {
        '1': '바른 자세로 생활하기',
        '2': '규칙적으로 가벼운 운동하기',
        '3': '바른 식습관 기르기',
        '4': '몸을 깨끗하게 하기',
        '5': '생활 주변을 깨끗하게 하기',
        '6': '마음 건강하게 관리하기'
    }
    
    for i in range(1, 7):
        reflections = DailyReflection.objects.filter(
            tracker=tracker,
            promise_number=i
        ).select_related('evaluation__teacher').order_by('week', 'day')
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        
        ref_list = []
        for ref in reflections:
            ref_data = {
                'id': ref.id,
                'week': ref.week,
                'day': ref.day,
                'day_name': days[ref.day - 1],
                'date': str(ref.reflection_date),
                'text': ref.reflection_text,
                'is_evaluated': hasattr(ref, 'evaluation')
            }
            
            if ref_data['is_evaluated']:
                ref_data['evaluation'] = {
                    'score': ref.evaluation.score,
                    'emoji': ref.evaluation.get_emoji_feedback_display(),
                    'comment': ref.evaluation.comment
                }
            
            ref_list.append(ref_data)
        
        # 약속 제목 가져오기
        promise_title = tracker.promises.get(str(i), default_promises.get(str(i), f'약속 {i}'))
        
        promises.append({
            'number': i,
            'title': promise_title,
            'reflections': ref_list
        })
    
    # 기존 평가 정보
    overall_eval = None
    if hasattr(tracker, 'overall_evaluation'):
        overall_eval = {
            'grade': tracker.overall_evaluation.grade,
            'badges': tracker.overall_evaluation.badges,
            'feedback': tracker.overall_evaluation.feedback
        }
    
    return JsonResponse({
        'success': True,
        'data': {
            'student_name': tracker.student.user.get_full_name(),
            'promises': promises,
            'final_reflection': tracker.final_reflection,
            'overall_evaluation': overall_eval,
            'is_submitted': tracker.is_submitted
        }
    })


@csrf_exempt
@login_required
def evaluate_reflection(request):
    """개별 소감 평가"""
    if request.method == 'POST':
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
        
        try:
            data = json.loads(request.body)
            reflection_id = data.get('reflection_id')
            
            reflection = get_object_or_404(DailyReflection, id=reflection_id)
            
            # 교사 권한 확인
            teacher = request.user.teacher
            if reflection.tracker.student.school_class not in teacher.classes.all():
                return JsonResponse({'error': '해당 학생을 평가할 권한이 없습니다.'}, status=403)
            
            # 평가 생성 또는 업데이트
            evaluation, _ = DailyReflectionEvaluation.objects.update_or_create(
                reflection=reflection,
                defaults={
                    'teacher': teacher,
                    'score': data.get('score'),
                    'emoji_feedback': data.get('emoji_feedback'),
                    'comment': data.get('comment', ''),
                    'has_stamp': data.get('has_stamp', False)
                }
            )
            
            reflection.is_evaluated = True
            reflection.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@login_required
def save_overall_evaluation(request):
    """종합 평가 저장"""
    if request.method == 'POST':
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
        
        try:
            data = json.loads(request.body)
            tracker_id = data.get('tracker_id')
            
            tracker = get_object_or_404(HealthHabitTracker, id=tracker_id)
            
            # 교사 권한 확인
            teacher = request.user.teacher
            if tracker.student.school_class not in teacher.classes.all():
                return JsonResponse({'error': '해당 학생을 평가할 권한이 없습니다.'}, status=403)
            
            # 총점 계산
            total_score = DailyReflectionEvaluation.objects.filter(
                reflection__tracker=tracker
            ).aggregate(total=Sum('score'))['total'] or 0
            
            # 평가 생성 또는 업데이트
            evaluation, _ = TrackerEvaluation.objects.update_or_create(
                tracker=tracker,
                defaults={
                    'teacher': teacher,
                    'grade': data.get('grade'),
                    'total_score': total_score,
                    'badges': data.get('badges', []),
                    'feedback': data.get('feedback')
                }
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)