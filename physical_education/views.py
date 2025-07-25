from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from teacher.decorators import teacher_required
from .models import (
    PAPSSession, PAPSSessionActivity, PAPSCategory, 
    PAPSActivity, PAPSRecord
)
from .forms import PAPSSessionForm, PAPSActivitySelectionForm
from .utils import calculate_paps_grade
import json


@login_required
@teacher_required
def teacher_dashboard(request):
    """체육 교사 대시보드 뷰"""
    teacher_id = request.user.teacher.id
    
    # 통계 데이터 계산
    total_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).count()
    
    # 진행 중인 측정회차 (완료되지 않은 회차)
    active_sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id,
        is_completed=False
    ).count()
    
    # 이번 달 측정회차
    from datetime import datetime
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    this_month_sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id,
        measurement_date__month=current_month,
        measurement_date__year=current_year
    ).count()
    
    # 총 측정 기록 수 (참여 학생 수로 사용)
    total_records = PAPSRecord.objects.filter(
        measured_by_teacher_id=teacher_id
    ).count()
    
    # 최근 측정회차 5개
    recent_sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id
    ).order_by('-created_at')[:5]
    
    # 각 측정회차별 진행률 계산
    session_progress = []
    for session in recent_sessions:
        # 해당 회차의 총 활동 수
        total_activities = PAPSSessionActivity.objects.filter(
            session_id=session.id
        ).count()
        
        # 측정 완료된 기록 수 (임시로 전체 기록 수 사용)
        completed_records = PAPSRecord.objects.filter(
            session_id=session.id
        ).count()
        
        # 진행률 계산 (임시로 간단한 계산)
        progress_percentage = min(100, (completed_records * 10)) if total_activities > 0 else 0
        
        session_progress.append({
            'session': session,
            'progress': progress_percentage,
            'total_activities': total_activities,
            'completed_records': completed_records
        })
    
    context = {
        "user": request.user,
        "stats": {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "this_month_sessions": this_month_sessions,
            "total_records": total_records,
        },
        "recent_sessions": session_progress,
    }
    return render(request, "physical_education/teachers/dashboard.html", context)


# ================= PAPS 측정회차 관리 =================

@login_required
@teacher_required
def paps_session_list_view(request):
    """PAPS 측정회차 목록/생성/삭제 통합 뷰"""
    teacher_id = request.user.teacher.id
    
    # AJAX 요청 확인
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # POST 요청 처리 (생성 또는 삭제)
    if request.method == 'POST':
        # 삭제 처리
        if 'delete' in request.POST:
            session_ids = request.POST.getlist('session_ids')
            if session_ids:
                deleted_count = 0
                errors = []
                for session_id in session_ids:
                    try:
                        session = PAPSSession.objects.get(
                            id=session_id,
                            teacher_id=teacher_id
                        )
                        # 완료된 세션은 삭제 불가
                        if session.is_completed:
                            error_msg = f'완료된 측정회차 "{session.name}"는 삭제할 수 없습니다.'
                            errors.append(error_msg)
                            messages.error(request, error_msg)
                            continue
                        # 관련 측정 기록이 있는지 확인
                        if PAPSRecord.objects.filter(session_id=session.id).exists():
                            error_msg = f'측정 기록이 있는 회차 "{session.name}"는 삭제할 수 없습니다.'
                            errors.append(error_msg)
                            messages.error(request, error_msg)
                            continue
                        
                        session_name = session.name
                        session.delete()
                        deleted_count += 1
                        messages.success(request, f'측정회차 "{session_name}"이 삭제되었습니다.')
                    except PAPSSession.DoesNotExist:
                        pass
                
                if deleted_count == 0:
                    messages.warning(request, '삭제된 측정회차가 없습니다.')
                
                if is_ajax:
                    return JsonResponse({
                        'success': deleted_count > 0,
                        'deleted_count': deleted_count,
                        'errors': errors
                    })
            else:
                messages.error(request, '삭제할 측정회차를 선택해주세요.')
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': '삭제할 측정회차를 선택해주세요.'
                    })
        
        # 생성 처리
        else:
            form = PAPSSessionForm(request.POST, teacher_id=teacher_id)
            if form.is_valid():
                session = form.save()
                messages.success(request, f'측정회차 "{session.name}"이 생성되었습니다.')
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'session': {
                            'id': str(session.id),
                            'school_year': session.school_year,
                            'session_type': session.session_type,
                            'session_type_display': session.get_session_type_display(),
                            'name': session.name,
                            'measurement_date': session.measurement_date.strftime('%Y-%m-%d'),
                            'is_completed': session.is_completed
                        }
                    })
                else:
                    return redirect('physical_education:paps_session_list')
            else:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'errors': form.errors
                    })
    else:
        form = PAPSSessionForm(teacher_id=teacher_id)
    
    # 필터링 파라미터
    filter_year = request.GET.get('year')
    filter_type = request.GET.get('type')
    
    # 세션 목록 조회
    sessions_qs = PAPSSession.objects.filter(teacher_id=teacher_id)
    
    # 필터링 적용
    if filter_year:
        sessions_qs = sessions_qs.filter(school_year=filter_year)
    if filter_type:
        sessions_qs = sessions_qs.filter(session_type=filter_type)
    
    sessions_qs = sessions_qs.order_by('-school_year', '-measurement_date')
    
    # AJAX 요청인 경우 JSON 응답
    if is_ajax and request.method == 'GET':
        sessions_data = []
        for session in sessions_qs:
            sessions_data.append({
                'id': str(session.id),
                'school_year': session.school_year,
                'session_type': session.session_type,
                'session_type_display': session.get_session_type_display(),
                'name': session.name,
                'measurement_date': session.measurement_date.strftime('%Y-%m-%d'),
                'is_completed': session.is_completed
            })
        return JsonResponse({
            'success': True,
            'sessions': sessions_data,
            'total': len(sessions_data)
        })
    
    # 페이지네이션 (일반 요청의 경우)
    paginator = Paginator(sessions_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 년도 범위 생성 (현재 년도 기준 ±5년)
    current_year = timezone.now().year
    year_range = range(current_year - 5, current_year + 6)
    
    context = {
        'page_obj': page_obj,
        'sessions': page_obj.object_list,
        'form': form,
        'year_range': year_range,
        'current_year': current_year,
    }
    return render(request, 'physical_education/teachers/paps/sessions/list.html', context)


# paps_session_create_view 제거됨 - paps_session_list_view에 통합

'''
@login_required
@teacher_required
def paps_session_create_view(request):
    """PAPS 측정회차 생성 뷰"""
    if request.method == 'POST':
        form = PAPSSessionForm(
            request.POST, 
            teacher_id=request.user.teacher.id
        )
        if form.is_valid():
            session = form.save()
            messages.success(request, f'측정회차 "{session.name}"이 생성되었습니다.')
            return redirect('physical_education:paps_session_list')
    else:
        form = PAPSSessionForm(teacher_id=request.user.teacher.id)
    
    context = {
        'form': form,
        'title': '측정회차 생성'
    }
    return render(request, 'physical_education/paps/sessions/create.html', context)
'''

# paps_session_delete_view 제거됨 - paps_session_list_view에 통합

'''
@login_required
@teacher_required
@require_POST
def paps_session_delete_view(request, session_id):
    """PAPS 측정회차 삭제 뷰"""
    session = get_object_or_404(
        PAPSSession,
        id=session_id,
        teacher_id=request.user.teacher.id
    )
    
    # 완료된 세션은 삭제 불가
    if session.is_completed:
        messages.error(request, '완료된 측정회차는 삭제할 수 없습니다.')
        return redirect('physical_education:paps_session_list')
    
    # 관련 측정 기록이 있는지 확인
    if PAPSRecord.objects.filter(session_id=session.id).exists():
        messages.error(request, '측정 기록이 있는 회차는 삭제할 수 없습니다.')
        return redirect('physical_education:paps_session_list')
    
    session_name = session.name
    session.delete()
    messages.success(request, f'측정회차 "{session_name}"이 삭제되었습니다.')
    return redirect('physical_education:paps_session_list')
'''


# ================= PAPS 측정종목 선택 =================

@login_required
@teacher_required
def paps_session_activities_view(request):
    """PAPS 측정종목 선택 뷰"""
    # 교사의 모든 측정회차 가져오기
    sessions = PAPSSession.objects.filter(
        teacher_id=request.user.teacher.id
    ).order_by('-created_at')
    
    # URL 파라미터 또는 POST에서 session_id 가져오기
    session_id = request.GET.get('session_id') or request.POST.get('session_id')
    session = None
    
    if session_id:
        session = get_object_or_404(
            PAPSSession,
            id=session_id,
            teacher_id=request.user.teacher.id
        )
        
        # 완료된 세션은 수정 불가
        if session.is_completed:
            messages.error(request, '완료된 측정회차의 종목은 수정할 수 없습니다.')
            return redirect('physical_education:paps_session_list')
    
    # session이 선택되지 않았을 때 처리
    if not session:
        context = {
            'sessions': sessions,
            'session': None,
        }
        return render(request, 'physical_education/paps/sessions/activities_selection.html', context)
    
    # 학년 선택 처리
    selected_grades = []
    if request.method == 'POST':
        selected_grades_str = request.POST.get('selected_grades', '')
        if selected_grades_str:
            try:
                selected_grades = [int(g) for g in selected_grades_str.split(',') if g.strip()]
            except ValueError:
                messages.error(request, '올바른 학년을 선택해주세요.')
                return redirect(f'{request.path}?session_id={session.id}')
        
        # 종목 선택 폼 처리
        if selected_grades and 'save_activities' in request.POST:
            form = PAPSActivitySelectionForm(
                request.POST,
                session=session,
                selected_grades=selected_grades
            )
            if form.is_valid():
                try:
                    with transaction.atomic():
                        saved_count = form.save_selections(session, selected_grades)
                        messages.success(
                            request, 
                            f'{len(selected_grades)}개 학년, {saved_count}개 종목이 저장되었습니다.'
                        )
                        return redirect(f'{request.path}?session_id={session.id}')
                except Exception as e:
                    messages.error(request, f'저장 중 오류가 발생했습니다: {str(e)}')
        else:
            # 학년 선택 후 폼 생성
            form = PAPSActivitySelectionForm(
                session=session,
                selected_grades=selected_grades
            )
    else:
        form = None
    
    # 기존 선택된 종목들 조회
    existing_activities = PAPSSessionActivity.objects.filter(
        session_id=session.id
    ).select_related('category_id', 'activity_id')
    
    # 카테고리별 활동 조회
    required_categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.REQUIRED
    ).order_by('order')
    
    optional_categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.OPTIONAL
    ).order_by('order')
    
    context = {
        'sessions': sessions,  # 모든 측정회차 목록 추가
        'session': session,
        'form': form,
        'selected_grades': selected_grades,
        'existing_activities': existing_activities,
        'required_categories': required_categories,
        'optional_categories': optional_categories,
        'grade_choices': PAPSSessionActivity.GRADE_CHOICES,
    }
    return render(request, 'physical_education/paps/sessions/activities_selection.html', context)


# ================= PAPS 측정 입력 =================



@login_required
@teacher_required
def paps_required_measurement_view(request):
    """PAPS 필수평가 측정 입력 뷰"""
    # 필수평가 카테고리 조회
    required_categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.REQUIRED
    ).order_by('order')
    
    context = {
        'categories': required_categories,
        'evaluation_type': 'required',
        'title': 'PAPS 필수평가 입력'
    }
    return render(request, 'physical_education/paps/measurement/input.html', context)


@login_required
@teacher_required
def paps_optional_measurement_view(request):
    """PAPS 선택평가 측정 입력 뷰"""
    # 선택평가 카테고리 조회
    optional_categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.OPTIONAL
    ).order_by('order')
    
    context = {
        'categories': optional_categories,
        'evaluation_type': 'optional',
        'title': 'PAPS 선택평가 입력'
    }
    return render(request, 'physical_education/paps/measurement/input.html', context)


# ================= PAPS API 엔드포인트 =================

@login_required
@teacher_required
@require_POST
@csrf_exempt
def api_paps_save_measurement(request):
    """PAPS 측정 데이터 저장 API"""
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id')
        student_id = data.get('student_id')
        activity_id = data.get('activity_id')
        measurement_data = data.get('measurement_data', {})
        
        # 유효성 검사
        if not all([session_id, student_id, activity_id]):
            return JsonResponse({
                'success': False,
                'error': '필수 파라미터가 누락되었습니다.'
            })
        
        # 권한 확인
        session = get_object_or_404(
            PAPSSession,
            id=session_id,
            teacher_id=request.user.teacher.id
        )
        
        activity = get_object_or_404(PAPSActivity, id=activity_id)
        
        # 학생 정보 확인 (실제 구현에서는 Student 모델 사용)
        # student = get_object_or_404(Student, id=student_id)
        # class_id = student.class_id
        # student_grade = student.grade
        
        # 임시로 하드코딩 (실제 구현에서는 위 코드 사용)
        class_id = 1
        student_grade = 6
        
        # 기존 기록 조회 또는 생성
        record, created = PAPSRecord.objects.get_or_create(
            session_id=session.id,
            student_id=student_id,
            activity_id=activity.id,
            defaults={
                'measured_by_teacher_id': request.user.teacher.id,
                'class_id': class_id,
                'student_grade': student_grade,
                'measurement_data': measurement_data,
            }
        )
        
        if not created:
            record.measurement_data = measurement_data
            record.measured_at = timezone.now()
            record.save()
        
        return JsonResponse({
            'success': True,
            'record_id': str(record.id),
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON 데이터가 올바르지 않습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def api_paps_calculate_grade(request):
    """PAPS 등급 계산 API"""
    try:
        if request.method == 'GET':
            data = request.GET
        else:
            data = json.loads(request.body)
        
        activity_id = data.get('activity_id')
        measurement_data = data.get('measurement_data', {})
        student_grade = int(data.get('student_grade', 6))
        
        if not activity_id:
            return JsonResponse({
                'success': False,
                'error': 'activity_id가 필요합니다.'
            })
        
        activity = get_object_or_404(PAPSActivity, id=activity_id)
        
        # 등급 계산
        grade_result = calculate_paps_grade(
            activity=activity,
            measurement_data=measurement_data,
            student_grade=student_grade
        )
        
        return JsonResponse({
            'success': True,
            'grade_result': grade_result
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON 데이터가 올바르지 않습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@teacher_required
def api_paps_get_activities(request, category):
    """카테고리별 PAPS 활동 목록 API"""
    try:
        category_obj = get_object_or_404(PAPSCategory, name=category)
        activities = PAPSActivity.objects.filter(category_id=category_obj.id)
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': str(activity.id),
                'name': activity.get_name_display(),
                'measurement_schema': activity.measurement_schema,
                'evaluation_criteria': activity.evaluation_criteria
            })
        
        return JsonResponse({
            'success': True,
            'activities': activities_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
