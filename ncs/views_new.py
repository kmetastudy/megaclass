# ncs/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.contrib import messages
from django.core.paginator import Paginator

from accounts.models import Student
from teacher.models import Contents, ContentType
from .models import (
    NCSCompetency, NCSLearningSession, NCSQuestion,
    NCSQuestionAttempt, NCSCompetencyAnalysis, NCSAssignment
)
import json
import random


@login_required
def student_dashboard(request):
    """학생 대시보드"""
    try:
        student = request.user.student
    except:
        messages.error(request, '학생 계정이 필요합니다.')
        return redirect('login')
    
    # 최근 학습 세션
    recent_sessions = NCSLearningSession.objects.filter(
        student=student
    ).order_by('-started_at')[:5]
    
    # 역량별 분석
    competency_analysis = NCSCompetencyAnalysis.objects.filter(
        student=student
    ).order_by('-weakness_score')[:10]
    
    # 할당된 과제
    assignments = NCSAssignment.objects.filter(
        Q(assigned_students=student) | Q(assigned_class=student.student_class),
        is_active=True,
        due_date__gte=timezone.now()
    ).distinct()
    
    context = {
        'student': student,
        'recent_sessions': recent_sessions,
        'competency_analysis': competency_analysis,
        'assignments': assignments,
    }
    
    return render(request, 'ncs/student_dashboard.html', context)


@login_required
def start_learning_session(request):
    """학습 세션 시작"""
    if request.method == 'POST':
        try:
            student = request.user.student
            session_type = request.POST.get('session_type', 'auto')
            question_count = int(request.POST.get('question_count', 10))
            
            # 세션 생성
            session = NCSLearningSession.objects.create(
                student=student,
                session_type=session_type,
                total_questions=question_count
            )
            
            # 문제 선택 로직
            if session_type == 'auto':
                questions = select_auto_questions(student, question_count)
            elif session_type == 'weakness':
                questions = select_weakness_questions(student, question_count)
            else:  # manual
                competency_ids = request.POST.getlist('competencies')
                questions = select_manual_questions(competency_ids, question_count)
            
            # 문제 할당
            competencies_set = set()
            for idx, content in enumerate(questions, 1):
                competency = get_competency_for_content(content)
                NCSQuestion.objects.create(
                    session=session,
                    content=content,
                    competency=competency,
                    order=idx
                )
                competencies_set.add(competency)
            
            # 세션에 역량 연결
            session.competencies.set(list(competencies_set))
            
            return redirect('ncs:learning_session', session_id=session.id)
            
        except Exception as e:
            messages.error(request, f'세션 시작 중 오류가 발생했습니다: {str(e)}')
            return redirect('ncs:student_dashboard')
    
    # GET 요청 - 세션 시작 페이지
    competencies = NCSCompetency.objects.filter(
        is_active=True,
        level=3  # 세분류만
    ).order_by('code')
    
    return render(request, 'ncs/start_session.html', {
        'competencies': competencies
    })


@login_required
def learning_session(request, session_id):
    """학습 세션 진행"""
    session = get_object_or_404(
        NCSLearningSession,
        id=session_id,
        student=request.user.student
    )
    
    if session.is_completed:
        return redirect('ncs:session_result', session_id=session.id)
    
    # 문제 목록 조회
    questions = session.questions.select_related(
        'content', 'competency'
    ).order_by('order')
    
    # 이미 답변한 문제들
    answered_questions = {}
    for question in questions:
        if question.is_answered:
            # 최신 시도 정보 가져오기
            latest_attempt = question.attempts.filter(
                student=request.user.student
            ).order_by('-attempt_number').first()
            
            answered_questions[str(question.id)] = {
                'student_answer': question.student_answer,
                'is_correct': question.is_correct,
                'correct_answer': question.content.answer,
                'attempt_count': question.current_attempt_count
            }
    
    # 진행률 계산
    progress_percent = (session.completed_questions / session.total_questions * 100) if session.total_questions > 0 else 0
    
    context = {
        'session': session,
        'questions': questions,
        'answered_questions': json.dumps(answered_questions),
        'progress_percent': progress_percent,
    }
    
    return render(request, 'ncs/learning_session.html', context)


@csrf_protect
@require_POST
def submit_answer(request, session_id, question_id):
    """답안 제출 (재시도 가능)"""
    try:
        # 세션과 문항 조회
        session = get_object_or_404(
            NCSLearningSession, 
            id=session_id, 
            student=request.user.student
        )
        
        question = get_object_or_404(
            NCSQuestion,
            id=question_id,
            session=session
        )
        
        # 요청 데이터 파싱
        answer = request.POST.get('answer')
        time_spent = int(request.POST.get('time_spent', 0))
        
        if not answer:
            return JsonResponse({
                'success': False,
                'message': '답안을 선택해주세요.'
            }, status=400)
        
        # 재시도 가능한 답안 체크
        result = question.check_answer_with_retry(answer, time_spent)
        
        # 세션 완료 확인
        session_completed = session.completed_questions >= session.total_questions
        if session_completed and not session.is_completed:
            session.is_completed = True
            session.completed_at = timezone.now()
            session.calculate_score()
            session.save()
            
            # 역량별 분석 업데이트
            update_competency_analysis(session)
        
        response_data = {
            'success': True,
            'is_correct': result['is_correct'],
            'correct_answer': result.get('correct_answer'),
            'attempt_count': result['attempt_count'],
            'can_retry': result['can_retry'],
            'session_completed': session_completed
        }
        
        if session_completed:
            response_data['score'] = session.score
            response_data['accuracy'] = round(
                (session.correct_answers / session.total_questions) * 100, 1
            ) if session.total_questions > 0 else 0
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_protect
@require_POST
def save_progress(request, session_id):
    """학습 진행 상황 저장"""
    try:
        session = get_object_or_404(
            NCSLearningSession,
            id=session_id,
            student=request.user.student
        )
        
        data = json.loads(request.body)
        
        # 세션 상태 업데이트
        session.time_spent = data.get('time_spent', session.time_spent)
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': '진행 상황이 저장되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_protect
@require_POST
def complete_session(request, session_id):
    """학습 세션 완료"""
    try:
        session = get_object_or_404(
            NCSLearningSession,
            id=session_id,
            student=request.user.student
        )
        
        if not session.is_completed:
            session.is_completed = True
            session.completed_at = timezone.now()
            session.calculate_score()
            session.save()
            
            # 역량별 분석 업데이트
            update_competency_analysis(session)
        
        return JsonResponse({
            'success': True,
            'score': session.score,
            'accuracy': round(
                (session.correct_answers / session.total_questions) * 100, 1
            ) if session.total_questions > 0 else 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def session_result(request, session_id):
    """학습 세션 결과"""
    session = get_object_or_404(
        NCSLearningSession,
        id=session_id,
        student=request.user.student
    )
    
    # 문제별 결과
    questions = session.questions.select_related(
        'content', 'competency'
    ).order_by('order')
    
    # 역량별 결과 집계
    competency_results = {}
    for question in questions:
        comp = question.competency
        if comp.id not in competency_results:
            competency_results[comp.id] = {
                'competency': comp,
                'total': 0,
                'correct': 0,
                'incorrect': 0
            }
        
        competency_results[comp.id]['total'] += 1
        if question.is_correct:
            competency_results[comp.id]['correct'] += 1
        else:
            competency_results[comp.id]['incorrect'] += 1
    
    # 시도 이력
    attempt_history = {}
    for question in questions:
        attempts = question.attempts.filter(
            student=request.user.student
        ).order_by('attempt_number')
        attempt_history[question.id] = attempts
    
    context = {
        'session': session,
        'questions': questions,
        'competency_results': competency_results.values(),
        'attempt_history': attempt_history,
    }
    
    return render(request, 'ncs/session_result.html', context)


@login_required
def competency_analysis(request):
    """역량 분석 상세"""
    student = request.user.student
    
    analyses = NCSCompetencyAnalysis.objects.filter(
        student=student
    ).select_related('competency').order_by('-weakness_score')
    
    # 페이지네이션
    paginator = Paginator(analyses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'analyses': page_obj,
        'total_competencies': analyses.count(),
    }
    
    return render(request, 'ncs/competency_analysis.html', context)


@login_required
def learning_history(request):
    """학습 이력"""
    student = request.user.student
    
    sessions = NCSLearningSession.objects.filter(
        student=student
    ).order_by('-started_at')
    
    # 필터링
    session_type = request.GET.get('type')
    if session_type:
        sessions = sessions.filter(session_type=session_type)
    
    date_from = request.GET.get('from')
    if date_from:
        sessions = sessions.filter(started_at__gte=date_from)
    
    date_to = request.GET.get('to')
    if date_to:
        sessions = sessions.filter(started_at__lte=date_to)
    
    # 페이지네이션
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sessions': page_obj,
        'total_sessions': sessions.count(),
    }
    
    return render(request, 'ncs/learning_history.html', context)


# 헬퍼 함수들
def select_auto_questions(student, count):
    """자동 문제 선택"""
    # 학생의 취약 역량 기반 선택
    weak_competencies = NCSCompetencyAnalysis.objects.filter(
        student=student
    ).order_by('-weakness_score')[:5].values_list('competency_id', flat=True)
    
    # 취약 역량 문제 우선 선택
    questions = list(Contents.objects.filter(
        content_type__type_name='ncs_question',
        is_active=True,
        competency_id__in=weak_competencies
    ).order_by('?')[:count//2])
    
    # 나머지는 랜덤 선택
    remaining_count = count - len(questions)
    if remaining_count > 0:
        exclude_ids = [q.id for q in questions]
        random_questions = Contents.objects.filter(
            content_type__type_name='ncs_question',
            is_active=True
        ).exclude(id__in=exclude_ids).order_by('?')[:remaining_count]
        questions.extend(list(random_questions))
    
    random.shuffle(questions)
    return questions[:count]


def select_weakness_questions(student, count):
    """취약점 보강 문제 선택"""
    # 정답률이 낮은 역량 위주
    weak_competencies = NCSCompetencyAnalysis.objects.filter(
        student=student,
        accuracy_rate__lt=70
    ).order_by('accuracy_rate')[:10].values_list('competency_id', flat=True)
    
    questions = list(Contents.objects.filter(
        content_type__type_name='ncs_question',
        is_active=True,
        competency_id__in=weak_competencies
    ).order_by('?')[:count])
    
    return questions


def select_manual_questions(competency_ids, count):
    """수동 선택 문제"""
    questions = list(Contents.objects.filter(
        content_type__type_name='ncs_question',
        is_active=True,
        competency_id__in=competency_ids
    ).order_by('?')[:count])
    
    return questions


def get_competency_for_content(content):
    """콘텐츠의 역량 매핑"""
    # 콘텐츠에 역량이 직접 연결되어 있다면 사용
    if hasattr(content, 'competency'):
        return content.competency
    
    # 아니면 기본 역량 반환 (실제 구현에서는 더 정교한 매핑 필요)
    return NCSCompetency.objects.filter(is_active=True).first()


def update_competency_analysis(session):
    """역량별 분석 데이터 업데이트"""
    # 세션의 각 역량별 결과 집계
    competency_results = session.questions.values('competency').annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
        avg_time=Avg('time_spent')
    )
    
    for result in competency_results:
        analysis, created = NCSCompetencyAnalysis.objects.get_or_create(
            student=session.student,
            competency_id=result['competency']
        )
        
        # 누적 데이터 업데이트
        analysis.total_attempts += result['total']
        analysis.correct_count += result['correct']
        analysis.incorrect_count += (result['total'] - result['correct'])
        analysis.average_time = result['avg_time'] or 0
        analysis.last_attempt_date = timezone.now()
        
        # 분석 업데이트
        analysis.update_analysis()