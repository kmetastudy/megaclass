from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Sum, Avg, F
from django.utils import timezone
from accounts.models import Student, Teacher, Class
from teacher.models import ChasiSlide
from .models import RollingAttempt, FeedbackCategory, RollingEvaluation
import json
from collections import Counter
import re
import csv

# 학생용 뷰 (기존 유지)
@login_required
def student_rolling_view(request, slide_id):
    """학생용 앞구르기 페이지"""
    if not hasattr(request.user, 'student'):
        return JsonResponse({'error': '학생만 접근 가능합니다.'}, status=403)
    
    student = request.user.student
    slide = get_object_or_404(ChasiSlide, id=slide_id)
    
    attempts = RollingAttempt.objects.filter(student=student).order_by('attempt_number')
    previous_feedback = None
    
    if attempts.exists():
        last_attempt = attempts.last()
        if not last_attempt.is_success and last_attempt.attempt_number < 5:
            previous_feedback = last_attempt.feedback
    
    context = {
        'slide_id': slide_id,
        'slide': slide,
        'student': student,
        'attempts': attempts,
        'previous_feedback': previous_feedback,
        'attempt_count': attempts.count(),
        'user': request.user,
    }
    return render(request, 'rolling/student_rolling.html', context)

@login_required
@csrf_exempt
def save_attempt(request, slide_id):
    """시도 저장"""
    if request.method == 'POST':
        if not hasattr(request.user, 'student'):
            return JsonResponse({'error': '학생만 저장 가능합니다.'}, status=403)
        
        try:
            data = json.loads(request.body)
            student = request.user.student
            
            attempt, created = RollingAttempt.objects.update_or_create(
                student=student,
                attempt_number=data.get('attempt_number'),
                defaults={
                    'is_success': data.get('is_success'),
                    'feedback': data.get('feedback')
                }
            )
            
            return JsonResponse({'success': True, 'created': created})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def get_student_attempts(request, slide_id):
    """학생의 시도 기록 조회"""
    if not hasattr(request.user, 'student'):
        return JsonResponse({'error': '학생만 접근 가능합니다.'}, status=403)
    
    student = request.user.student
    attempts = RollingAttempt.objects.filter(student=student).order_by('attempt_number')
    
    data = []
    for attempt in attempts:
        data.append({
            'attempt_number': attempt.attempt_number,
            'is_success': attempt.is_success,
            'feedback': attempt.feedback,
            'created_at': attempt.created_at.isoformat()
        })
    
    return JsonResponse({'success': True, 'attempts': data})

# 수정된 교사용 대시보드
@login_required
def teacher_dashboard(request):
    """교사 대시보드 (개선된 버전)"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    teacher_classes = teacher.classes.all()
    
    # 각 학급별 평가 진행률 계산
    for cls in teacher_classes:
        total_students = cls.student_set.count()
        evaluated_students = RollingEvaluation.objects.filter(
            student__school_class=cls
        ).count()
        cls.evaluation_rate = int((evaluated_students / total_students * 100) if total_students > 0 else 0)
    
    # 회차별 성공률 통계
    success_stats = []
    for i in range(1, 6):
        total_attempts = RollingAttempt.objects.filter(
            attempt_number=i,
            student__school_class__in=teacher_classes
        ).count()
        
        success_attempts = RollingAttempt.objects.filter(
            attempt_number=i,
            is_success=True,
            student__school_class__in=teacher_classes
        ).count()
        
        success_rate = int((success_attempts / total_attempts * 100) if total_attempts > 0 else 0)
        success_stats.append({
            'attempt': i,
            'count': success_attempts,
            'success_rate': success_rate
        })
    
    context = {
        'teacher_classes': teacher_classes,
        'success_stats': json.dumps(success_stats),
    }
    return render(request, 'rolling/teacher_dashboard.html', context)

# 통합된 학급 평가 뷰
@login_required
def teacher_class_evaluation_view(request, class_id):
    """학급별 평가 관리 통합 뷰"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    school_class = get_object_or_404(Class, id=class_id)
    
    # 권한 확인
    if school_class not in request.user.teacher.classes.all():
        return JsonResponse({'error': '담당 학급만 조회 가능합니다.'}, status=403)
    
    students = Student.objects.filter(school_class=school_class).select_related('user')
    
    # 평가 진행률 계산
    total_students = students.count()
    evaluated_students = RollingEvaluation.objects.filter(
        student__school_class=school_class
    ).count()
    evaluation_rate = int((evaluated_students / total_students * 100) if total_students > 0 else 0)
    
    # 학생 데이터 준비
    student_data = []
    for student in students:
        attempts = RollingAttempt.objects.filter(student=student)
        success_count = attempts.filter(is_success=True).count()
        
        # 기존 평가 확인
        try:
            evaluation = student.rolling_evaluation
        except RollingEvaluation.DoesNotExist:
            evaluation = None
        
        student_data.append({
            'id': student.id,
            'name': student.user.get_full_name(),
            'student_id': student.student_id,
            'attempt_count': attempts.count(),
            'success_count': success_count,
            'has_evaluation': evaluation is not None,
            'evaluation': evaluation
        })
    
    context = {
        'school_class': school_class,
        'students': student_data,
        'evaluation_rate': evaluation_rate,
    }
    return render(request, 'rolling/teacher_class_evaluation.html', context)

# API: 학급 통계
@login_required
def api_class_stats(request, class_id):
    """학급 통계 API"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    school_class = get_object_or_404(Class, id=class_id)
    
    # 권한 확인
    if school_class not in request.user.teacher.classes.all():
        return JsonResponse({'error': '담당 학급만 조회 가능합니다.'}, status=403)
    
    total_students = school_class.student_set.count()
    evaluations = RollingEvaluation.objects.filter(student__school_class=school_class)
    
    stats = {
        'total_students': total_students,
        'evaluated': evaluations.count(),
        'not_evaluated': total_students - evaluations.count(),
        'grade_a': evaluations.filter(grade='A').count(),
        'grade_b': evaluations.filter(grade='B').count(),
        'grade_c': evaluations.filter(grade='C').count(),
        'grade_d': evaluations.filter(grade='D').count(),
    }
    
    return JsonResponse(stats)

# API: 학생 시도 기록
@login_required
def api_student_attempts(request, student_id):
    """특정 학생의 시도 기록 API"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    student = get_object_or_404(Student, id=student_id)
    
    # 권한 확인
    if student.school_class not in request.user.teacher.classes.all():
        return JsonResponse({'error': '담당 학급의 학생만 조회 가능합니다.'}, status=403)
    
    attempts = RollingAttempt.objects.filter(student=student).order_by('attempt_number')
    
    data = []
    for attempt in attempts:
        data.append({
            'attempt_number': attempt.attempt_number,
            'is_success': attempt.is_success,
            'feedback': attempt.feedback,
            'created_at': attempt.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({'attempts': data})

@csrf_exempt
@login_required
def save_evaluation(request, student_id):
    """평가 저장"""
    if request.method == 'POST':
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'error': '교사만 평가 가능합니다.'}, status=403)
        
        try:
            data = json.loads(request.body)
            student = get_object_or_404(Student, id=student_id)
            
            # 권한 확인
            if student.school_class not in request.user.teacher.classes.all():
                return JsonResponse({'error': '담당 학급의 학생만 평가 가능합니다.'}, status=403)
            
            evaluation, created = RollingEvaluation.objects.update_or_create(
                student=student,
                defaults={
                    'teacher': request.user.teacher,
                    'grade': data.get('grade'),
                    'overall_feedback': data.get('overall_feedback')
                }
            )
            
            return JsonResponse({'success': True, 'created': created})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def get_feedback_analysis(request):
    """피드백 분석 (개선된 버전)"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher_classes = request.user.teacher.classes.all()
    
    # 담당 학급 학생들의 피드백만 분석
    success_feedbacks = RollingAttempt.objects.filter(
        is_success=True,
        student__school_class__in=teacher_classes
    ).values_list('feedback', flat=True)
    
    fail_feedbacks = RollingAttempt.objects.filter(
        is_success=False,
        student__school_class__in=teacher_classes
    ).values_list('feedback', flat=True)
    
    # 키워드 기반 분류
    success_categories = {
        '균형 유지': ['균형', '중심', '안정'],
        '속도 조절': ['속도', '빠르', '천천히', '조절'],
        '자세': ['자세', '몸', '구부리', '펴기'],
        '호흡': ['호흡', '숨'],
    }
    
    fail_categories = {
        '균형 문제': ['균형', '넘어', '쓰러'],
        '속도 문제': ['빠르', '느리', '속도'],
        '자세 문제': ['자세', '굽히', '펴기', '몸'],
        '두려움': ['무서', '두려', '겁'],
    }
    
    def categorize_and_calculate_percentage(feedbacks, categories):
        counts = {cat: 0 for cat in categories}
        
        for feedback in feedbacks:
            for category, keywords in categories.items():
                if any(keyword in feedback for keyword in keywords):
                    counts[category] += 1
                    break
        
        total = sum(counts.values())
        percentages = {}
        for cat, count in counts.items():
            percentages[cat] = int((count / total * 100) if total > 0 else 0)
        
        return percentages
    
    success_factors = categorize_and_calculate_percentage(success_feedbacks, success_categories)
    fail_factors = categorize_and_calculate_percentage(fail_feedbacks, fail_categories)
    
    return JsonResponse({
        'success_factors': success_factors,
        'fail_factors': fail_factors
    })

# 평가 결과 내보내기
@login_required
def export_evaluations(request, class_id):
    """학급 평가 결과를 CSV로 내보내기"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    school_class = get_object_or_404(Class, id=class_id)
    
    # 권한 확인
    if school_class not in request.user.teacher.classes.all():
        return JsonResponse({'error': '담당 학급만 내보낼 수 있습니다.'}, status=403)
    
    # CSV 응답 생성
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rolling_evaluation_{school_class.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff'.encode('utf8'))  # UTF-8 BOM
    
    writer = csv.writer(response)
    writer.writerow(['번호', '이름', '학번', '시도 횟수', '성공 횟수', '등급', '종합 피드백', '평가일'])
    
    students = Student.objects.filter(school_class=school_class).select_related('user')
    
    for idx, student in enumerate(students, 1):
        attempts = RollingAttempt.objects.filter(student=student)
        success_count = attempts.filter(is_success=True).count()
        
        try:
            evaluation = student.rolling_evaluation
            grade = evaluation.get_grade_display()
            feedback = evaluation.overall_feedback
            eval_date = evaluation.evaluated_at.strftime('%Y-%m-%d')
        except RollingEvaluation.DoesNotExist:
            grade = '미평가'
            feedback = ''
            eval_date = ''
        
        writer.writerow([
            idx,
            student.user.get_full_name(),
            student.student_id,
            attempts.count(),
            success_count,
            grade,
            feedback,
            eval_date
        ])
    
    return response