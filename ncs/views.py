from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from teacher.decorators import teacher_required
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from django.contrib import messages
import json
import random

from .models import (
    # NCSCompetency, NCSLearningSession, NCSQuestion,
    # NCSCompetencyAnalysis, NCSAssignment, NCSClassStatistics,
    NCSCompetency, NCSLearningSession, NCSQuestion,
    NCSCompetencyAnalysis, NCSAssignment, NCSClassStatistics,
    NCSQuestionAttempt, NCSStudentAnswer  # 추가
)
from teacher.models import Contents, ContentType
from accounts.models import Student, Teacher,Class
# from student.models import StudentAnswer
from django.views.decorators.csrf import csrf_protect



@csrf_protect
@require_POST
def save_progress(request, session_id):
    """학습 진행 상황 자동 저장"""
    # 디버깅용 로그 추가
    print(f"[Save Progress Debug]")
    print(f"  - Session ID: {session_id}")
    print(f"  - User: {request.user}")
    print(f"  - User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    print(f"  - Referer: {request.META.get('HTTP_REFERER', 'Unknown')}")
    print(f"  - Request Time: {timezone.now()}")
    
    try:
        student = request.user.student
        session = NCSLearningSession.objects.get(
            id=session_id,
            student=student
        )
        
        # 이미 완료된 세션인지 확인 - 조건 완화
        if session.is_completed:
            # 완료된 세션의 경우 에러가 아닌 정보성 메시지로 변경
            return JsonResponse({
                'success': True,  # False -> True로 변경
                'message': '완료된 세션입니다.',
                'error_code': 'SESSION_COMPLETED'
            }, status=200)  # 400 -> 200으로 변경
        
        data = json.loads(request.body)
        
        # 세션 진행 상황 업데이트
        current_progress = data.get('current_progress', 0)
        
        # 진행률이 감소하지 않도록 확인
        if current_progress >= session.completed_questions:
            session.completed_questions = current_progress
            session.save()
        
        return JsonResponse({
            'success': True,
            'message': '진행 상황이 저장되었습니다.',
            'current_progress': session.completed_questions
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '학생 정보를 찾을 수 없습니다.',
            'error_code': 'STUDENT_NOT_FOUND'
        }, status=400)
    except NCSLearningSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '세션을 찾을 수 없습니다.',
            'error_code': 'SESSION_NOT_FOUND'
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '잘못된 요청 데이터입니다.',
            'error_code': 'INVALID_JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'error_code': 'UNKNOWN_ERROR'
        }, status=500)

@csrf_protect
@require_POST
def save_progress_062609(request, session_id):
    """학습 진행 상황 자동 저장"""
    """학습 진행 상황 자동 저장"""
    # 디버깅용 로그 추가
    print(f"[Save Progress Debug]")
    print(f"  - Session ID: {session_id}")
    print(f"  - User: {request.user}")
    print(f"  - User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    print(f"  - Referer: {request.META.get('HTTP_REFERER', 'Unknown')}")
    print(f"  - Request Time: {timezone.now()}")
    
    try:
        student = request.user.student
        session = NCSLearningSession.objects.get(
            id=session_id,
            student=student
        )
        
        # 이미 완료된 세션인지 확인
        if session.is_completed:
            return JsonResponse({
                'success': False,
                'message': '이미 완료된 세션입니다.',
                'error_code': 'SESSION_COMPLETED'
            }, status=400)
        
        data = json.loads(request.body)
        
        # 세션 진행 상황 업데이트
        current_progress = data.get('current_progress', 0)
        
        # 진행률이 감소하지 않도록 확인
        if current_progress >= session.completed_questions:
            session.completed_questions = current_progress
            session.save()
        
        return JsonResponse({
            'success': True,
            'message': '진행 상황이 저장되었습니다.',
            'current_progress': session.completed_questions
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '학생 정보를 찾을 수 없습니다.',
            'error_code': 'STUDENT_NOT_FOUND'
        }, status=400)  # 404 → 400으로 변경
    except NCSLearningSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '세션을 찾을 수 없습니다.',
            'error_code': 'SESSION_NOT_FOUND'
        }, status=400)  # 404 → 400으로 변경
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '잘못된 요청 데이터입니다.',
            'error_code': 'INVALID_JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'error_code': 'UNKNOWN_ERROR'
        }, status=500)
    

# save_progress 수정
@csrf_protect
@require_POST
def save_progress_0626_04(request, session_id):
    """학습 진행 상황 자동 저장"""
    try:
        student = request.user.student  # student 객체 먼저 가져오기
        session = NCSLearningSession.objects.get(
            id=session_id,
            student=student  # 수정됨
        )
        
        data = json.loads(request.body)
        
        # 세션 진행 상황 업데이트
        session.completed_questions = data.get('current_progress', 0)
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': '진행 상황이 저장되었습니다.'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '학생 정보를 찾을 수 없습니다.'
        }, status=404)
    except NCSLearningSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '세션을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_protect
@require_POST
def save_progress_0626(request, session_id):
    """학습 진행 상황 자동 저장"""
    try:
        session = NCSLearningSession.objects.get(
            id=session_id,
            student=request.user.student  # ✅ 수정됨
        )
        
        data = json.loads(request.body)
        
        # 세션 진행 상황 업데이트
        session.completed_questions = data.get('current_progress', 0)
        session.save()
        
        # 선택한 답안들을 임시 저장 (필요한 경우)
        # 이 부분은 프로젝트 구조에 따라 구현
        
        return JsonResponse({
            'success': True,
            'message': '진행 상황이 저장되었습니다.'
        })
        
    except NCSLearningSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '세션을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)



# complete_session 수정
@csrf_protect
@require_POST
def complete_session(request, session_id):
    """학습 세션 완료 처리"""
    try:
        student = request.user.student
        session = NCSLearningSession.objects.get(
            id=session_id,
            student=student  # 수정됨
        )
        
        # 세션 완료 처리
        session.is_completed = True
        session.completed_at = timezone.now()
        
        # 점수 계산 - NCSStudentAnswer 모델 사용
        correct_answers = NCSStudentAnswer.objects.filter(
            session=session,
            is_correct=True
        ).count()
        
        total_questions = session.total_questions
        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        accuracy = round((correct_answers / total_questions) * 100, 1) if total_questions > 0 else 0
        
        session.score = score
        session.save()
        
        return JsonResponse({
            'success': True,
            'score': score,
            'accuracy': accuracy,
            'message': '학습이 완료되었습니다.'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '학생 정보를 찾을 수 없습니다.'
        }, status=404)
    except NCSLearningSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '세션을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_protect
@require_POST
def complete_session_0626(request, session_id):
    """학습 세션 완료 처리"""
    try:
        session = NCSLearningSession.objects.get(
            id=session_id,
            student=request.user
        )
        
        # 세션 완료 처리
        session.is_completed = True
        session.completed_at = timezone.now()
        
        # 점수 계산
        correct_answers = NCSStudentAnswer.objects.filter(
            session=session,
            is_correct=True
        ).count()
        
        total_questions = session.total_questions
        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        accuracy = round((correct_answers / total_questions) * 100, 1) if total_questions > 0 else 0
        
        session.score = score
        session.save()
        
        return JsonResponse({
            'success': True,
            'score': score,
            'accuracy': accuracy,
            'message': '학습이 완료되었습니다.'
        })
        
    except NCSLearningSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '세션을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
def student_dashboard(request):
    """학생 개인별 NCS 대시보드"""
    student = request.user.student
    
    # 전체 역량 분석 데이터
    analyses = NCSCompetencyAnalysis.objects.filter(
        student=student
    ).select_related('competency').order_by('-weakness_score')[:10]
    
    # 최근 학습 세션
    recent_sessions = NCSLearningSession.objects.filter(
        student=student
    ).order_by('-started_at')[:5]
    
    # 전체 통계
    total_stats = NCSLearningSession.objects.filter(
        student=student,
        is_completed=True
    ).aggregate(
        total_questions=Sum('total_questions'),
        total_correct=Sum('correct_answers'),
        avg_score=Avg('score')
    )
    
    # 역량별 차트 데이터
    competency_data = []
    for analysis in analyses[:5]:  # 상위 5개 취약 역량
        competency_data.append({
            'name': analysis.competency.competency_name,
            'accuracy': round(analysis.accuracy_rate, 1),
            'attempts': analysis.total_attempts,
            'weakness': round(analysis.weakness_score, 1)
        })
    
    # 활성 과제
    active_assignments = NCSAssignment.objects.filter(
        Q(assigned_students=student) | Q(assigned_class=student.school_class),
        is_active=True,
        due_date__gte=timezone.now()
    ).distinct()[:3]
    
    context = {
        'student': student,
        'analyses': analyses,
        'recent_sessions': recent_sessions,
        'total_stats': total_stats,
        'competency_data': json.dumps(competency_data),
        'active_assignments': active_assignments,
        'overall_accuracy': round(total_stats['avg_score'] or 0, 1),
    }
    
    return render(request, 'ncs/student_dashboard.html', context)


@login_required
def create_learning_session(request):
    """학습 세션 생성"""
    student = request.user.student
    
    if request.method == 'POST':
        session_type = request.POST.get('session_type', 'manual')
        competency_ids = request.POST.getlist('competencies')
        question_count = int(request.POST.get('question_count', 10))
        
        try:
            # 세션 생성
            session = NCSLearningSession.objects.create(
                student=student,
                session_type=session_type,
                total_questions=question_count
            )
            
            # 컴피턴시 설정
            if session_type == 'weakness':
                # 취약점 기반 자동 선택
                weak_competencies = NCSCompetencyAnalysis.objects.filter(
                    student=student,
                    accuracy_rate__lt=70  # 70% 미만 정답률
                ).order_by('-weakness_score')[:5]  # 최대 5개로 증가
                
                if weak_competencies.exists():
                    for analysis in weak_competencies:
                        session.competencies.add(analysis.competency)
                    messages.success(request, f'{weak_competencies.count()}개의 취약 역량에서 문제를 출제합니다.')
                else:
                    # 취약 역량이 없는 경우 - 전체 역량에서 랜덤 선택
                    messages.info(request, '아직 취약한 역량이 없어 전체 역량에서 문제를 출제합니다.')
                    random_competencies = NCSCompetency.objects.filter(
                        is_active=True, 
                        level=3
                    ).order_by('?')[:5]
                    
                    for comp in random_competencies:
                        session.competencies.add(comp)
                    
            elif session_type == 'auto':
                # 자동 선택 - 랜덤하게 역량 선택
                random_competencies = NCSCompetency.objects.filter(
                    is_active=True,
                    level=3
                ).order_by('?')[:5]
                
                for comp in random_competencies:
                    session.competencies.add(comp)
                    
            else:
                # 수동 선택
                if competency_ids:
                    competencies = NCSCompetency.objects.filter(id__in=competency_ids)
                    session.competencies.set(competencies)
                else:
                    # 역량을 선택하지 않은 경우 랜덤 선택
                    messages.warning(request, '역량을 선택하지 않아 전체 역량에서 문제를 출제합니다.')
                    random_competencies = NCSCompetency.objects.filter(
                        is_active=True,
                        level=3
                    ).order_by('?')[:5]
                    
                    for comp in random_competencies:
                        session.competencies.add(comp)
            
            # 문제 생성
            generate_questions(session, question_count)
            
            # 문제가 생성되지 않은 경우
            if session.questions.count() == 0:
                session.delete()
                messages.error(request, '문제를 생성할 수 없습니다. 콘텐츠가 부족합니다.')
                return redirect('ncs:create_session')
            
            # 실제 생성된 문제 수로 업데이트
            actual_count = session.questions.count()
            if actual_count < question_count:
                messages.warning(request, f'요청한 {question_count}문제 중 {actual_count}문제만 생성되었습니다.')
                session.total_questions = actual_count
                session.save()
            
            return redirect('ncs:learning_session', session_id=session.id)
            
        except Exception as e:
            if 'session' in locals():
                session.delete()
            messages.error(request, f'세션 생성 중 오류가 발생했습니다: {str(e)}')
            return redirect('ncs:create_session')
    
    # GET 요청 - 세션 생성 페이지
    competencies = NCSCompetency.objects.filter(
        is_active=True,
        level=3  # 세분류만
    ).order_by('main_category', 'sub_category', 'competency_name')
    
    # 취약 역량 추천
    weak_analyses = NCSCompetencyAnalysis.objects.filter(
        student=student,
        accuracy_rate__lt=70
    ).select_related('competency').order_by('-weakness_score')[:5]
    
    # 학습 이력이 있는지 확인
    has_learning_history = NCSCompetencyAnalysis.objects.filter(student=student).exists()
    
    context = {
        'competencies': competencies,
        'weak_analyses': weak_analyses,
        'question_counts': [5, 10, 15, 20, 30],
        'has_learning_history': has_learning_history,  # 추가
    }
    
    return render(request, 'ncs/create_session.html', context)

@login_required
def create_learning_session_0625(request):
    """학습 세션 생성"""
    student = request.user.student
    
    if request.method == 'POST':
        session_type = request.POST.get('session_type', 'manual')
        competency_ids = request.POST.getlist('competencies')
        question_count = int(request.POST.get('question_count', 10))
        
        try:
            # 세션 생성
            session = NCSLearningSession.objects.create(
                student=student,
                session_type=session_type,
                total_questions=question_count
            )
            
            # 컴피턴시 설정
            if session_type == 'weakness':
                # 취약점 기반 자동 선택
                weak_competencies = NCSCompetencyAnalysis.objects.filter(
                    student=student,
                    accuracy_rate__lt=70  # 70% 미만 정답률
                ).order_by('-weakness_score')[:3]
                
                for analysis in weak_competencies:
                    session.competencies.add(analysis.competency)
                
                # 취약 역량이 없는 경우 메시지
                if not weak_competencies.exists():
                    messages.info(request, '아직 취약한 역량이 없어 전체 역량에서 문제를 출제합니다.')
                    
            elif session_type == 'auto':
                # 자동/랜덤 선택은 generate_questions에서 처리
                pass
            else:
                # 수동 선택
                if competency_ids:
                    competencies = NCSCompetency.objects.filter(id__in=competency_ids)
                    session.competencies.set(competencies)
                else:
                    messages.warning(request, '역량을 선택하지 않아 전체 역량에서 문제를 출제합니다.')
            
            # 문제 생성
            generate_questions(session, question_count)
            
            # 문제가 생성되지 않은 경우
            if session.questions.count() == 0:
                session.delete()
                messages.error(request, '문제를 생성할 수 없습니다. 콘텐츠가 부족합니다.')
                return redirect('ncs:create_session')
            
            return redirect('ncs:learning_session', session_id=session.id)
            
        except Exception as e:
            messages.error(request, f'세션 생성 중 오류가 발생했습니다: {str(e)}')
            return redirect('ncs:create_session')
    
    # GET 요청 - 세션 생성 페이지
    competencies = NCSCompetency.objects.filter(
        is_active=True,
        level=3  # 세분류만
    ).order_by('main_category', 'sub_category', 'competency_name')
    
    # 취약 역량 추천
    weak_analyses = NCSCompetencyAnalysis.objects.filter(
        student=student,
        accuracy_rate__lt=70
    ).select_related('competency').order_by('-weakness_score')[:5]
    
    context = {
        'competencies': competencies,
        'weak_analyses': weak_analyses,
        'question_counts': [5, 10, 15, 20, 30],
    }
    
    return render(request, 'ncs/create_session.html', context)

# views.py의 generate_questions 함수 수정
def generate_questions(session, count):
    """세션에 문제 생성 - sub_competency 기반 검색"""
    competencies = session.competencies.all()
    
    # 역량이 없는 경우 처리
    if not competencies.exists():
        if session.session_type == 'weakness':
            competencies = NCSCompetency.objects.filter(is_active=True, level=3).order_by('?')[:5]
        else:
            competencies = NCSCompetency.objects.filter(is_active=True, level=3).order_by('?')[:10]
    
    if not competencies.exists():
        raise ValueError("문제를 생성할 역량이 없습니다.")
    
    # 각 역량별로 균등하게 문제 선택
    competency_list = list(competencies)
    questions_per_competency = max(1, count // len(competency_list))
    remaining = count % len(competency_list)
    
    order = 1
    created_questions = 0
    
    for idx, competency in enumerate(competency_list):
        # sub_competency로 정확한 검색
        print(f"\n[Searching] Competency: {competency.competency_name}")
        
        # 1차: JSONField 직접 검색 (PostgreSQL)
        contents = Contents.objects.filter(
            content_type__type_name='multiple-choice',
            is_active=True,
            tags__sub_competency=competency.competency_name
        )
        
        # 2차: contains 검색 (다른 DB)
        if not contents.exists():
            contents = Contents.objects.filter(
                content_type__type_name='multiple-choice',
                is_active=True,
                tags__contains={'sub_competency': competency.competency_name}
            )
            
        # 3차: 문자열 검색
        if not contents.exists():
            contents = Contents.objects.filter(
                content_type__type_name='multiple-choice',
                is_active=True
            ).extra(
                where=["tags::text LIKE %s"],
                params=[f'%"sub_competency":"{competency.competency_name}"%']
            )
        
        print(f"  Found {contents.count()} contents")
        
        if not contents.exists():
            print(f"  Warning: No contents found for {competency.competency_name}")
            continue
        
        # 문항 수 결정
        num_questions = questions_per_competency
        if idx < remaining:
            num_questions += 1
        
        # 랜덤 선택
        selected_contents = list(contents.order_by('?')[:num_questions])
        
        # NCSQuestion 생성
        for content in selected_contents:
            # 디버깅: content 내용 확인
            print(f"  Creating question from content ID {content.id}: {content.title}")
            print(f"    Tags: {content.tags}")
            print(f"    Page content exists: {bool(content.page)}")
            print(f"    Answer: {content.answer}")
            
            NCSQuestion.objects.create(
                session=session,
                content=content,
                competency=competency,
                order=order
            )
            order += 1
            created_questions += 1
    
    # 실제 생성된 문항 수로 업데이트
    session.total_questions = created_questions
    session.save()
    
    print(f"\n[Complete] Created {created_questions} questions for session {session.id}")

def generate_questions_0626(session, count):
    """세션에 문제 생성"""
    competencies = session.competencies.all()
    
    # 역량이 없는 경우 처리
    if not competencies.exists():
        # 세션 타입에 따른 처리
        if session.session_type == 'weakness':
            # 취약점 학습인데 취약 역량이 없는 경우, 전체 역량에서 랜덤 선택
            messages.warning(session.student.user, '아직 취약한 역량이 없어 전체 역량에서 문제를 출제합니다.')
            competencies = NCSCompetency.objects.filter(is_active=True, level=3).order_by('?')[:5]
        else:
            # 일반적인 경우 전체 역량에서 선택
            competencies = NCSCompetency.objects.filter(is_active=True, level=3).order_by('?')[:10]
    
    # 여전히 역량이 없다면 에러 처리
    if not competencies.exists():
        # 최소한의 기본 역량 생성 또는 에러 메시지
        raise ValueError("문제를 생성할 역량이 없습니다. 관리자에게 문의하세요.")
    
    # 각 역량별로 균등하게 문제 선택
    competency_list = list(competencies)
    questions_per_competency = max(1, count // len(competency_list))
    remaining = count % len(competency_list)
    
    order = 1
    created_questions = 0
    
    for idx, competency in enumerate(competency_list):
        # 해당 역량의 콘텐츠 찾기
        contents = Contents.objects.filter(
            content_type__type_name='multiple-choice',
            is_active=True,
            tags__icontains=competency.code  # contains 대신 icontains 사용
        )
        
        # 콘텐츠가 없는 경우 다른 방법으로 찾기
        if not contents.exists():
            # 역량명으로도 검색
            contents = Contents.objects.filter(
                content_type__type_name='multiple-choice',
                is_active=True,
                tags__icontains=competency.competency_name
            )
        
        # 그래도 없으면 건너뛰기
        if not contents.exists():
            continue
        
        # 문항 수 결정
        num_questions = questions_per_competency
        if idx < remaining:
            num_questions += 1
        
        # 랜덤 선택
        selected_contents = list(contents.order_by('?')[:num_questions])
        
        # NCSQuestion 생성
        for content in selected_contents:
            NCSQuestion.objects.create(
                session=session,
                content=content,
                competency=competency,
                order=order
            )
            order += 1
            created_questions += 1
    
    # 생성된 문항이 요청한 수보다 적은 경우 추가 생성
    if created_questions < count:
        # 전체 콘텐츠에서 추가 선택
        all_contents = Contents.objects.filter(
            content_type__type_name='multiple-choice',
            is_active=True
        ).exclude(
            id__in=session.questions.values_list('content_id', flat=True)
        ).order_by('?')[:count - created_questions]
        
        # 기본 역량 할당 (첫 번째 역량 사용)
        default_competency = competency_list[0] if competency_list else NCSCompetency.objects.filter(is_active=True).first()
        
        for content in all_contents:
            NCSQuestion.objects.create(
                session=session,
                content=content,
                competency=default_competency,
                order=order
            )
            order += 1
            created_questions += 1
    
    # 실제 생성된 문항 수로 업데이트
    session.total_questions = created_questions
    session.save()


# views.py - learning_session 함수를 하나로 정리
@login_required
def learning_session(request, session_id):
    """학습 세션 진행 (원페이지)"""
    student = request.user.student
    session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
    
    # 세션 완료 확인
    if session.is_completed:
        return redirect('ncs:session_result', session_id=session.id)
    
    # 모든 문제 가져오기
    questions = session.questions.select_related(
        'content', 'content__content_type', 'competency'
    ).order_by('order')
    
    # 기존 답변 데이터 조회 - NCSStudentAnswer 모델 사용
    answered_questions = {}
    student_answers = NCSStudentAnswer.objects.filter(
        session=session,
        student=request.user
    ).select_related('question')
    
    for sa in student_answers:
        # 정답 형식 정규화
        correct_answer = sa.question.content.answer
        if isinstance(correct_answer, str) and correct_answer.startswith('{'):
            try:
                parsed = json.loads(correct_answer)
                correct_answer = parsed.get('answer', correct_answer)
            except:
                pass
                
        answered_questions[str(sa.question.id)] = {
            'student_answer': sa.answer,
            'correct_answer': str(correct_answer),
            'is_correct': sa.is_correct
        }
    
    # 각 문제에 대한 데이터를 준비
    questions_data = []
    for question in questions:
        # tags 처리
        tags = question.content.tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = {}
        elif tags is None:
            tags = {}
        
        # answer 처리
        answer = question.content.answer
        if isinstance(answer, str) and answer.startswith('{'):
            try:
                answer_data = json.loads(answer)
                answer = answer_data.get('answer', answer)
            except:
                pass
        
        # 문제 HTML에서 선택지 추출 (서버사이드)
        content_html = question.content.page or ""
        choices = []
        
        # 선택지 패턴 매칭
        import re
        patterns = [
            re.compile(r'([①②③④⑤])\s*([^①②③④⑤]+)', re.DOTALL),
            re.compile(r'(\d+)\)\s*([^\d]+?)(?=\d+\)|$)', re.DOTALL),
        ]
        
        for pattern in patterns:
            matches = pattern.findall(content_html)
            if matches:
                for match in matches:
                    choices.append({
                        'number': match[0],
                        'text': match[1].strip()
                    })
                break
        
        questions_data.append({
            'id': question.id,
            'order': question.order,
            'content_id': question.content.id,
            'title': question.content.title,
            'page': content_html,
            'answer': str(answer),  # 문자열로 변환
            'tags': tags,
            'choices': choices,  # 서버에서 추출한 선택지
            'competency': {
                'id': question.competency.id,
                'name': question.competency.competency_name,
                'code': question.competency.code
            },
            'is_answered': question.is_answered,
            'student_answer': question.student_answer,
            'is_correct': question.is_correct
        })
    
    context = {
        'session': session,
        'questions': questions,
        'questions_json': json.dumps(questions_data, ensure_ascii=False),
        'answered_questions': json.dumps(answered_questions, ensure_ascii=False),  # 추가
        'current_question_num': session.completed_questions + 1,
        'progress_percent': (session.completed_questions / session.total_questions * 100) if session.total_questions > 0 else 0,
    }
    
    return render(request, 'ncs/learning_session.html', context)
@login_required
def learning_session_0626__(request, session_id):
    """학습 세션 진행 (원페이지)"""
    student = request.user.student
    session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
    
    # 세션 완료 확인
    if session.is_completed:
        return redirect('ncs:session_result', session_id=session.id)
    
    # 모든 문제 가져오기
    questions = session.questions.select_related(
        'content', 'content__content_type', 'competency'
    ).order_by('order')
    
    # 각 문제에 대한 데이터를 준비
    questions_data = []
    for question in questions:
        # tags 처리
        tags = question.content.tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = {}
        elif tags is None:
            tags = {}
        
        # answer 처리
        answer = question.content.answer
        if isinstance(answer, str) and answer.startswith('{'):
            try:
                answer_data = json.loads(answer)
                answer = answer_data.get('answer', answer)
            except:
                pass
        
        # 문제 HTML에서 선택지 추출 (서버사이드)
        content_html = question.content.page or ""
        choices = []
        
        # 선택지 패턴 매칭
        import re
        patterns = [
            re.compile(r'([①②③④⑤])\s*([^①②③④⑤]+)', re.DOTALL),
            re.compile(r'(\d+)\)\s*([^\d]+?)(?=\d+\)|$)', re.DOTALL),
        ]
        
        for pattern in patterns:
            matches = pattern.findall(content_html)
            if matches:
                for match in matches:
                    choices.append({
                        'number': match[0],
                        'text': match[1].strip()
                    })
                break
        
        questions_data.append({
            'id': question.id,
            'order': question.order,
            'content_id': question.content.id,
            'title': question.content.title,
            'page': content_html,
            'answer': str(answer),  # 문자열로 변환
            'tags': tags,
            'choices': choices,  # 서버에서 추출한 선택지
            'competency': {
                'id': question.competency.id,
                'name': question.competency.competency_name,
                'code': question.competency.code
            },
            'is_answered': question.is_answered,
            'student_answer': question.student_answer,
            'is_correct': question.is_correct
        })
    
    context = {
        'session': session,
        'questions': questions,
        'questions_json': json.dumps(questions_data, ensure_ascii=False),
        'current_question_num': session.completed_questions + 1,
        'progress_percent': (session.completed_questions / session.total_questions * 100) if session.total_questions > 0 else 0,
    }
    
    return render(request, 'ncs/learning_session.html', context)


# views.py의 learning_session 함수 수정
@login_required
def learning_session_062608(request, session_id):
    """학습 세션 진행 (원페이지)"""
    student = request.user.student
    session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
    
    # 세션 완료 확인
    if session.is_completed:
        return redirect('ncs:session_result', session_id=session.id)
    
    # 모든 문제 가져오기 - content의 page와 tags 정보 포함
    questions = session.questions.select_related(
        'content', 'content__content_type', 'competency'
    ).order_by('order')
    
    # 각 문제에 대한 추가 정보 처리
    questions_data = []
    for question in questions:
        # tags가 문자열인 경우 JSON으로 파싱
        tags = question.content.tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = {}
        
        # answer가 JSON 형태인 경우 처리
        answer = question.content.answer
        if isinstance(answer, str) and answer.startswith('{'):
            try:
                answer_data = json.loads(answer)
                answer = answer_data.get('answer', answer)
            except:
                pass
        
        questions_data.append({
            'id': question.id,
            'order': question.order,
            'content_id': question.content.id,
            'title': question.content.title,
            'page': question.content.page,  # HTML 내용
            'answer': answer,
            'tags': tags,
            'competency': {
                'id': question.competency.id,
                'name': question.competency.competency_name,
                'code': question.competency.code
            },
            'is_answered': question.is_answered,
            'student_answer': question.student_answer,
            'is_correct': question.is_correct
        })
    
    context = {
        'session': session,
        'questions': questions,
        'questions_json': json.dumps(questions_data, ensure_ascii=False),
        'current_question_num': session.completed_questions + 1,
        'progress_percent': (session.completed_questions / session.total_questions * 100) if session.total_questions > 0 else 0,
    }
    
    return render(request, 'ncs/learning_session.html', context)

@login_required
def learning_session_06260740(request, session_id):
    """학습 세션 진행 (원페이지)"""
    student = request.user.student
    session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
    
    # 세션 완료 상태 확인 및 동기화
    if session.completed_questions >= session.total_questions and not session.is_completed:
        # 데이터 불일치 수정
        session.is_completed = True
        session.completed_at = timezone.now()
        session.calculate_score()
        session.save()
        return redirect('ncs:session_result', session_id=session.id)
    
    # 이미 완료된 세션인 경우
    if session.is_completed:
        return redirect('ncs:session_result', session_id=session.id)
    
    # 모든 문제 가져오기
    questions = session.questions.select_related(
        'content', 'competency'
    ).order_by('order')
    
    # 현재 진행 상황
    current_question_num = session.completed_questions + 1
    
    # 각 문제의 답변 상태를 JSON으로 준비
    answered_questions = {}
    for question in questions:
        if question.is_answered:
            answered_questions[str(question.id)] = {
                'student_answer': question.student_answer,
                'is_correct': question.is_correct,
                'correct_answer': question.content.answer
            }
    
    context = {
        'session': session,
        'questions': questions,
        'current_question_num': current_question_num,
        'progress_percent': (session.completed_questions / session.total_questions * 100) if session.total_questions > 0 else 0,
        'answered_questions': json.dumps(answered_questions),
    }
    
    return render(request, 'ncs/learning_session.html', context)


@login_required
def learning_session_0625(request, session_id):
    """학습 세션 진행 (원페이지)"""
    student = request.user.student
    session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
    
    # 모든 문제 가져오기
    questions = session.questions.select_related(
        'content', 'competency'
    ).order_by('order')
    
    # 현재 진행 상황
    current_question_num = session.completed_questions + 1
    if current_question_num > session.total_questions:
        # 이미 완료된 세션
        return redirect('ncs:session_result', session_id=session.id)
    
    context = {
        'session': session,
        'questions': questions,
        'current_question_num': current_question_num,
        'progress_percent': (session.completed_questions / session.total_questions * 100) if session.total_questions > 0 else 0,
    }
    
    return render(request, 'ncs/learning_session.html', context)


# submit_answer 수정
@require_POST
@login_required
def submit_answer(request, session_id, question_id):
    """답안 제출 (재시도 가능)"""
    try:
        student = request.user.student
        session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
        question = get_object_or_404(NCSQuestion, id=question_id, session=session)
        
        # 세션이 이미 완료된 경우
        if session.is_completed:
            return JsonResponse({
                'success': False,
                'message': '이미 완료된 세션입니다.'
            }, status=400)
        
        answer = request.POST.get('answer')
        time_spent = int(request.POST.get('time_spent', 0))
        
        print(f"[Submit Answer] Question {question_id}, Answer: {answer}, Time: {time_spent}s")
        
        # NCSStudentAnswer 사용
        student_answer, created = NCSStudentAnswer.objects.get_or_create(
            session=session,
            question=question,
            student=request.user,
            defaults={
                'answer': answer,
                'time_spent': time_spent
            }
        )
        
        # 재시도인 경우 답안 업데이트
        if not created:
            student_answer.answer = answer
            student_answer.time_spent = time_spent
            student_answer.attempt_count = student_answer.attempt_count + 1
            student_answer.submitted_at = timezone.now()
        
        # 정답 확인 및 정규화
        correct_answer = question.content.answer
        if isinstance(correct_answer, str) and correct_answer.startswith('{'):
            try:
                correct_data = json.loads(correct_answer)
                correct_answer = str(correct_data.get('answer', correct_answer))
            except:
                pass
        
        # 문자열로 비교
        correct_answer = str(correct_answer).strip()
        answer = str(answer).strip()
        
        is_correct = (answer == correct_answer)
        print(f"[Submit Answer] Correct answer: {correct_answer}, Is correct: {is_correct}")
        
        student_answer.is_correct = is_correct
        student_answer.save()
        
        # NCSQuestion 업데이트 (첫 제출인 경우만)
        if created:
            question.is_answered = True
            question.student_answer = answer
            question.is_correct = is_correct
            question.answered_at = timezone.now()
            question.time_spent = time_spent
            question.save()
            
            # 세션 진행률 업데이트
            session.completed_questions += 1
            if is_correct:
                session.correct_answers += 1
            session.save()
            
            print(f"[Submit Answer] Session progress: {session.completed_questions}/{session.total_questions}")
        
        # 역량 분석 업데이트
        analysis, _ = NCSCompetencyAnalysis.objects.get_or_create(
            student=student,
            competency=question.competency
        )
        
        if created:  # 첫 제출인 경우만 통계 업데이트
            analysis.total_attempts += 1
            if is_correct:
                analysis.correct_count += 1
            else:
                analysis.incorrect_count += 1
            analysis.last_attempt_date = timezone.now()
            analysis.update_analysis()
        
        # 세션 완료 확인
        session_completed = session.completed_questions >= session.total_questions
        if session_completed and not session.is_completed:
            session.is_completed = True
            session.completed_at = timezone.now()
            session.calculate_score()
            session.save()
            print(f"[Submit Answer] Session completed! Score: {session.score}")
        
        response_data = {
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'session_completed': session_completed,
            'attempt_count': student_answer.attempt_count,
            'score': session.score if session_completed else None
        }
        
        print(f"[Submit Answer] Response: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"[Submit Answer Error] {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    
@require_POST
@login_required
def submit_answer_0626(request, session_id, question_id):
    """답안 제출 (재시도 가능)"""
    try:
        student = request.user.student
        session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
        question = get_object_or_404(NCSQuestion, id=question_id, session=session)
        
        answer = request.POST.get('answer')
        time_spent = int(request.POST.get('time_spent', 0))
        
        # NCSStudentAnswer 사용
        student_answer, created = NCSStudentAnswer.objects.get_or_create(
            session=session,
            question=question,
            student=request.user,
            defaults={
                'answer': answer,
                'time_spent': time_spent
            }
        )
        
        # 재시도인 경우 답안 업데이트
        if not created:
            student_answer.answer = answer
            student_answer.time_spent = time_spent
            student_answer.attempt_count = student_answer.attempt_count + 1
            student_answer.submitted_at = timezone.now()
        
        # 정답 확인
        correct_answer = question.content.answer
        if isinstance(correct_answer, str) and correct_answer.startswith('{'):
            try:
                correct_data = json.loads(correct_answer)
                correct_answer = correct_data.get('answer', correct_answer)
            except:
                pass
        
        is_correct = str(answer) == str(correct_answer)
        student_answer.is_correct = is_correct
        student_answer.save()
        
        # NCSQuestion 업데이트
        if created:  # 첫 제출인 경우만
            question.is_answered = True
            question.student_answer = answer
            question.is_correct = is_correct
            question.answered_at = timezone.now()
            question.time_spent = time_spent
            question.save()
            
            # 세션 진행률 업데이트
            session.completed_questions += 1
            if is_correct:
                session.correct_answers += 1
            session.save()
        
        # 역량 분석 업데이트
        analysis, _ = NCSCompetencyAnalysis.objects.get_or_create(
            student=student,
            competency=question.competency
        )
        
        if created:  # 첫 제출인 경우만 통계 업데이트
            analysis.total_attempts += 1
            if is_correct:
                analysis.correct_count += 1
            else:
                analysis.incorrect_count += 1
            analysis.last_attempt_date = timezone.now()
            analysis.update_analysis()
        
        # 세션 완료 확인
        session_completed = session.completed_questions >= session.total_questions
        if session_completed and not session.is_completed:
            session.is_completed = True
            session.completed_at = timezone.now()
            session.calculate_score()
            session.save()
        
        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'session_completed': session_completed,
            'attempt_count': student_answer.attempt_count,
            'score': session.score if session_completed else None
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def submit_answer_0626(request, session_id, question_id):
    """답안 제출 (재시도 가능하도록 수정)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
    
    try:
        session = NCSLearningSession.objects.get(
            id=session_id,
            student=request.user
        )
        
        question = NCSQuestion.objects.get(id=question_id)
        
        answer = request.POST.get('answer')
        time_spent = int(request.POST.get('time_spent', 0))
        
        # 기존 답안이 있는지 확인
        student_answer, created = NCSStudentAnswer.objects.get_or_create(
            session=session,
            question=question,
            defaults={
                'student': request.user,
                'answer': answer,
                'time_spent': time_spent
            }
        )
        
        # 재시도인 경우 답안 업데이트
        if not created:
            student_answer.answer = answer
            student_answer.time_spent = time_spent
            student_answer.attempt_count = student_answer.attempt_count + 1
            student_answer.submitted_at = timezone.now()
        
        # 정답 확인
        correct_answer = question.correct_answer
        if isinstance(correct_answer, str) and correct_answer.startswith('{'):
            try:
                correct_data = json.loads(correct_answer)
                correct_answer = correct_data.get('answer', correct_answer)
            except:
                pass
        
        is_correct = str(answer) == str(correct_answer)
        student_answer.is_correct = is_correct
        student_answer.save()
        
        # 세션 진행률 업데이트 (재시도가 아닌 첫 제출인 경우만)
        if created:
            session.completed_questions += 1
            session.save()
        
        # 세션 완료 확인
        session_completed = session.completed_questions >= session.total_questions
        
        response_data = {
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'session_completed': session_completed,
            'attempt_count': student_answer.attempt_count
        }
        
        if session_completed:
            response_data['score'] = calculate_session_score(session)
        
        return JsonResponse(response_data)
        
    except (NCSLearningSession.DoesNotExist, NCSQuestion.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': '세션 또는 문제를 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    
def calculate_session_score(session):
    """세션 점수 계산"""
    correct_answers = NCSStudentAnswer.objects.filter(
        session=session,
        is_correct=True
    ).count()
    
    total_questions = session.total_questions
    
    if total_questions > 0:
        return int((correct_answers / total_questions) * 100)
    return 0


@require_POST
@login_required
def submit_answer_062523(request, session_id, question_id):
    """답안 제출 (AJAX)"""
    print(f"\n=== submit_answer 뷰 시작 ===")
    print(f"Session ID: {session_id}")
    print(f"Question ID: {question_id}")
    print(f"POST data: {request.POST}")
    
    student = request.user.student
    session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
    question = get_object_or_404(NCSQuestion, id=question_id, session=session)
    
    print(f"Student: {student}")
    print(f"Question order: {question.order}")
    print(f"Content ID: {question.content.id}")
    
    if question.is_answered:
        print("Error: 이미 답변한 문제")
        return JsonResponse({
            'success': False,
            'message': '이미 답변한 문제입니다.'
        })
    
    answer = request.POST.get('answer')
    time_spent = int(request.POST.get('time_spent', 0))
    
    print(f"Student answer: {answer}")
    print(f"Time spent: {time_spent}")
    
    # 답안 채점
    question.time_spent = time_spent
    is_correct = question.check_answer(answer)
    
    print(f"Correct answer: {question.content.answer}")
    print(f"Is correct: {is_correct}")
    
    # 역량 분석 업데이트
    analysis, created = NCSCompetencyAnalysis.objects.get_or_create(
        student=student,
        competency=question.competency
    )
    
    analysis.total_attempts += 1
    if is_correct:
        analysis.correct_count += 1
    else:
        analysis.incorrect_count += 1
    analysis.last_attempt_date = timezone.now()
    analysis.update_analysis()
    
    print(f"Analysis updated - Total attempts: {analysis.total_attempts}")
    
    # 세션 완료 체크
    if session.completed_questions >= session.total_questions:
        session.is_completed = True
        session.completed_at = timezone.now()
        session.calculate_score()
        session.save()
        print(f"Session completed! Final score: {session.score}")
    
    response_data = {
        'success': True,
        'is_correct': is_correct,
        'correct_answer': question.content.answer,
        'session_completed': session.is_completed,
        'score': round(session.score, 1) if session.is_completed else None
    }
    
    print(f"Response data: {response_data}")
    print("=== submit_answer 뷰 종료 ===\n")
    
    return JsonResponse(response_data)

@require_POST
@login_required
def submit_answer_0625(request, session_id, question_id):
    """답안 제출 (AJAX)"""
    student = request.user.student
    session = get_object_or_404(NCSLearningSession, id=session_id, student=student)
    question = get_object_or_404(NCSQuestion, id=question_id, session=session)
    
    if question.is_answered:
        return JsonResponse({
            'success': False,
            'message': '이미 답변한 문제입니다.'
        })
    
    answer = request.POST.get('answer')
    time_spent = int(request.POST.get('time_spent', 0))
    
    # 답안 채점
    question.time_spent = time_spent
    is_correct = question.check_answer(answer)
    
    # 역량 분석 업데이트
    analysis, created = NCSCompetencyAnalysis.objects.get_or_create(
        student=student,
        competency=question.competency
    )
    
    analysis.total_attempts += 1
    if is_correct:
        analysis.correct_count += 1
    else:
        analysis.incorrect_count += 1
    analysis.last_attempt_date = timezone.now()
    analysis.update_analysis()
    
    # 세션 완료 체크
    if session.completed_questions >= session.total_questions:
        session.is_completed = True
        session.completed_at = timezone.now()
        session.calculate_score()
        session.save()
    
    return JsonResponse({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': question.content.answer,
        'session_completed': session.is_completed,
        'score': round(session.score, 1) if session.is_completed else None
    })
@login_required
def session_result(request, session_id):
    """학습 세션 결과"""
    from django.db.models import F, FloatField, Case, When, Value
    from django.db.models.functions import Cast
    
    student = request.user.student
    
    try:
        session = NCSLearningSession.objects.get(
            id=session_id, 
            student=student
        )
    except NCSLearningSession.DoesNotExist:
        messages.error(request, '해당 학습 세션을 찾을 수 없습니다.')
        return redirect('ncs:student_dashboard')
    
    # 세션 완료 상태 확인 및 동기화
    if session.completed_questions >= session.total_questions and not session.is_completed:
        # 데이터 불일치 수정
        session.is_completed = True
        session.completed_at = timezone.now()
        session.calculate_score()
        session.save()
    
    # 세션이 완료되지 않았다면 학습 페이지로 리다이렉트
    if not session.is_completed:
        messages.warning(request, '아직 완료되지 않은 학습입니다. 모든 문제를 풀어주세요.')
        return redirect('ncs:learning_session', session_id=session_id)
    
    # 역량별 결과 집계 - 수정된 부분
    competency_results = session.questions.values(
        'competency__competency_name'
    ).annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
        # accuracy를 직접 계산하는 방식으로 변경
        accuracy=Case(
            When(total__gt=0, then=Cast(Count('id', filter=Q(is_correct=True)), FloatField()) * 100.0 / Cast(Count('id'), FloatField())),
            default=Value(0.0),
            output_field=FloatField()
        )
    )
    
    # 또는 더 간단한 방법으로:
    competency_results = []
    competencies = session.questions.values('competency__competency_name').annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True))
    )
    
    for comp in competencies:
        comp['accuracy'] = (comp['correct'] / comp['total'] * 100) if comp['total'] > 0 else 0
        competency_results.append(comp)
    
    # 총 소요 시간 계산
    total_time = sum(q.time_spent for q in session.questions.all())
    
    # 시간 표시를 위한 계산
    if total_time >= 3600:
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        time_display = f"{hours}시간 {minutes}분"
    elif total_time >= 60:
        minutes = total_time // 60
        seconds = total_time % 60
        time_display = f"{minutes}분 {seconds}초"
    else:
        time_display = f"{total_time}초"
    
    # 평균 소요 시간
    avg_time_per_question = total_time // session.total_questions if session.total_questions > 0 else 0
    
    # 점수 관련 계산
    score_percentage = float(session.score) if session.score else 0.0
    score_circle_value = score_percentage * 5.024  # 원형 그래프를 위한 계산
    
    # 점수에 따른 색상 결정
    if score_percentage >= 80:
        score_color = '#10b981'  # green
        score_color_class = 'text-green-600'
    elif score_percentage >= 60:
        score_color = '#f59e0b'  # yellow
        score_color_class = 'text-yellow-600'
    else:
        score_color = '#ef4444'  # red
        score_color_class = 'text-red-600'
    
    # 오답 수 계산
    wrong_answers = session.total_questions - session.correct_answers
    
    context = {
        'session': session,
        'competency_results': competency_results,
        'total_time': total_time,
        'time_display': time_display,
        'avg_time_per_question': avg_time_per_question,
        'score_percentage': score_percentage,
        'score_circle_value': score_circle_value,
        'score_color': score_color,
        'score_color_class': score_color_class,
        'wrong_answers': wrong_answers,
    }
    
    return render(request, 'ncs/session_result.html', context)


# ncs/views.py의 teacher_dashboard 함수 수정
@login_required
@teacher_required
def teacher_dashboard(request):
    """NCS 교사 대시보드 (통계 페이지)"""
    teacher = request.user.teacher
    
    # ===== 디버깅 로그 시작 =====
    print("="*50)
    print("NCS TEACHER DASHBOARD DEBUG")
    print("="*50)
    print(f"Teacher: {teacher}")
    print(f"Teacher ID: {teacher.id}")
    print(f"Teacher School: {teacher.school}")
    
    # 교사가 속한 반 조회
    classes = Class.objects.filter(teachers=teacher)
    print(f"\n[Classes Query] Class.objects.filter(teachers={teacher})")
    print(f"Classes Count: {classes.count()}")
    print("Classes List:")
    for cls in classes:
        print(f"  - {cls.id}: {cls.name} (학교: {cls.school})")
    
    # 역량 데이터 조회 - 수정된 부분
    try:
        # NCSCompetency로 수정 (Competency가 아님)
        competencies = NCSCompetency.objects.filter(is_active=True)
        print(f"\n[Competencies Query] NCSCompetency.objects.filter(is_active=True)")
        print(f"Competencies Count: {competencies.count()}")
        print("Competencies List:")
        for comp in competencies[:10]:  # 처음 10개만 출력
            print(f"  - {comp.id}: {comp.competency_name} (Code: {comp.code}, Level: {comp.level})")
            
        # 레벨별 역량 수 확인
        level_counts = NCSCompetency.objects.filter(is_active=True).values('level').annotate(count=Count('level'))
        print("\n[Competencies by Level]:")
        for lc in level_counts:
            print(f"  - Level {lc['level']}: {lc['count']} 개")
            
    except Exception as e:
        print(f"\n[ERROR] Failed to load competencies: {e}")
        import traceback
        print(traceback.format_exc())
        competencies = []
    
    # 필터 파라미터 확인
    filters = {
        'class_id': request.GET.get('class_id', ''),
        'competency_id': request.GET.get('competency_id', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }
    print(f"\n[Filters] GET parameters: {filters}")
    
    # 학생 통계 쿼리
    student_stats_query = NCSCompetencyAnalysis.objects.filter(
        student__school_class__teachers=teacher
    )
    
    # 필터 적용
    if filters['class_id']:
        student_stats_query = student_stats_query.filter(student__school_class_id=filters['class_id'])
    if filters['competency_id']:
        student_stats_query = student_stats_query.filter(competency_id=filters['competency_id'])
    
    # 통계 데이터
    stats = student_stats_query.aggregate(
        total_students=Count('student', distinct=True),
        avg_accuracy=Avg('accuracy_rate'),
        total_attempts=Sum('total_attempts'),
        avg_weakness=Avg('weakness_score')
    )
    
    print(f"\n[Stats Query Result]:")
    print(f"  - Total Students: {stats['total_students']}")
    print(f"  - Avg Accuracy: {stats['avg_accuracy']}")
    print(f"  - Total Attempts: {stats['total_attempts']}")
    print(f"  - Avg Weakness: {stats['avg_weakness']}")
    
    # 학생별 상세 통계
    student_stats = student_stats_query.values(
        'student__id',
        'student__user__first_name',
        'student__user__last_name',
        'student__school_class__name'
    ).annotate(
        avg_accuracy=Avg('accuracy_rate'),
        total_attempts=Sum('total_attempts'),
        weak_count=Count('id', filter=Q(accuracy_rate__lt=70))
    ).order_by('-weak_count', 'avg_accuracy')
    
    print(f"\n[Student Stats Count]: {student_stats.count()}")
    
    # Context 데이터 확인
    context = {
        'teacher': teacher,
        'classes': classes,
        'competencies': competencies,
        'filters': filters,
        'stats': stats,
        'student_stats': student_stats,
    }
    
    print(f"\n[Context Keys] {list(context.keys())}")
    print(f"[Context - classes] Type: {type(context['classes'])}, Count: {context['classes'].count()}")
    print(f"[Context - competencies] Type: {type(context['competencies'])}, Count: {competencies.count() if hasattr(competencies, 'count') else len(competencies)}")
    print("="*50)
    # ===== 디버깅 로그 끝 =====
    
    return render(request, 'ncs/teacher_dashboard.html', context)

@login_required
@teacher_required
def create_assignment(request):
    """과제 생성"""
    teacher = request.user.teacher
    
    if request.method == 'POST':
        assignment = NCSAssignment.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            assignment_type=request.POST.get('assignment_type'),
            teacher=teacher,
            question_count=int(request.POST.get('question_count', 10)),
            due_date=request.POST.get('due_date') or None
        )
        
        # 역량 설정
        competency_ids = request.POST.getlist('competencies')
        assignment.competencies.set(competency_ids)
        
        # 학생/반 할당
        if assignment.assignment_type == 'class':
            class_id = request.POST.get('class_id')
            if class_id:
                assignment.assigned_class_id = class_id
                assignment.save()
        else:
            student_ids = request.POST.getlist('students')
            assignment.assigned_students.set(student_ids)
        
        messages.success(request, '과제가 생성되었습니다.')
        return redirect('ncs:teacher_dashboard')
    
     # GET 요청
    competencies = NCSCompetency.objects.filter(is_active=True, level=3)
    classes = teacher.classes.all()
    students = Student.objects.filter(school_class__in=classes)
    
    context = {
        'competencies': competencies,
        'classes': classes,
        'students': students,
    }
    
    return render(request, 'ncs/create_assignment.html', context)


@login_required
@teacher_required
def statistics_view(request):
    """통계 상세 보기"""
    teacher = request.user.teacher
    
    # 필터 파라미터
    class_id = request.GET.get('class_id')
    competency_id = request.GET.get('competency_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # 기본 쿼리셋
    analyses = NCSCompetencyAnalysis.objects.filter(
        student__school_class__teachers=teacher
    )
    
    # 필터 적용
    if class_id:
        analyses = analyses.filter(student__school_class_id=class_id)
    if competency_id:
        analyses = analyses.filter(competency_id=competency_id)
    
    # 집계
    stats = analyses.aggregate(
        total_students=Count('student', distinct=True),
        avg_accuracy=Avg('accuracy_rate'),
        total_attempts=Sum('total_attempts'),
        avg_weakness=Avg('weakness_score')
    )
    
    # 학생별 상세
    student_stats = analyses.values(
        'student__user__first_name',
        'student__user__last_name',
        'student__school_class__name'
    ).annotate(
        avg_accuracy=Avg('accuracy_rate'),
        total_attempts=Sum('total_attempts'),
        weak_count=Count('id', filter=Q(accuracy_rate__lt=70))
    ).order_by('-weak_count', 'avg_accuracy')
    
    context = {
        'stats': stats,
        'student_stats': student_stats,
        'classes': teacher.classes.all(),
        'competencies': NCSCompetency.objects.filter(is_active=True),
        'filters': {
            'class_id': class_id,
            'competency_id': competency_id,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'ncs/statistics.html', context)

# views.py에 추가
@login_required
def api_contents_by_subcompetency(request):
    """sub_competency 기반 콘텐츠 검색 API"""
    sub_competency = request.GET.get('sub_competency', '')
    
    if not sub_competency:
        return JsonResponse({'error': 'sub_competency parameter is required'}, status=400)
    
    # JSONField 검색
    contents = Contents.objects.filter(
        content_type__type_name='multiple-choice',
        is_active=True,
        tags__sub_competency=sub_competency
    ).values('id', 'title', 'tags')[:20]
    
    # 검색 결과가 없으면 contains로 재검색
    if not contents:
        contents = Contents.objects.filter(
            content_type__type_name='multiple-choice',
            is_active=True,
            tags__icontains=f'"sub_competency":"{sub_competency}"'
        ).values('id', 'title', 'tags')[:20]
    
    data = []
    for content in contents:
        tags = content.get('tags', {})
        data.append({
            'id': content['id'],
            'title': content['title'],
            'competency': tags.get('competency', ''),
            'sub_competency': tags.get('sub_competency', ''),
            'difficulty': tags.get('difficulty', ''),
            'question_type': tags.get('question_type', '')
        })
    
    return JsonResponse({
        'results': data,
        'count': len(data)
    })


# API 뷰들
@login_required
def api_competency_search(request):
    """역량 검색 API"""
    query = request.GET.get('q', '')
    competencies = NCSCompetency.objects.filter(
        Q(competency_name__icontains=query) |
        Q(code__icontains=query),
        is_active=True,
        level=3
    )[:20]
    
    data = [{
        'id': c.id,
        'code': c.code,
        'name': c.competency_name,
        'category': f"{c.main_category} > {c.sub_category}"
    } for c in competencies]
    
    return JsonResponse({'results': data})


@login_required
def api_student_progress(request, student_id):
    """학생 진행 상황 API"""
    student = get_object_or_404(Student, id=student_id)
    
    # 권한 체크
    if hasattr(request.user, 'teacher'):
        if student.school_class not in request.user.teacher.classes.all():
            return JsonResponse({'error': '권한이 없습니다.'}, status=403)
    elif hasattr(request.user, 'student'):
        if request.user.student != student:
            return JsonResponse({'error': '권한이 없습니다.'}, status=403)
    
    # 역량별 분석 데이터
    analyses = NCSCompetencyAnalysis.objects.filter(
        student=student
    ).select_related('competency')
    
    data = {
        'student': {
            'id': student.id,
            'name': student.user.get_full_name(),
            'class': student.school_class.name
        },
        'competencies': [{
            'id': a.competency.id,
            'name': a.competency.competency_name,
            'accuracy': round(a.accuracy_rate, 1),
            'attempts': a.total_attempts,
            'weakness_score': round(a.weakness_score, 1)
        } for a in analyses],
        'summary': {
            'total_attempts': sum(a.total_attempts for a in analyses),
            'avg_accuracy': round(sum(a.accuracy_rate * a.total_attempts for a in analyses) / sum(a.total_attempts for a in analyses), 1) if analyses else 0
        }
    }
    
    return JsonResponse(data)