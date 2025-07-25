"""
PAPS 관련 API 엔드포인트
측정종목선택 관련 AJAX 요청을 처리합니다.
"""

import json
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from teacher.decorators import teacher_required
from .models import (
    PAPSSession, PAPSSessionActivity, PAPSCategory, 
    PAPSActivity
)
from .forms import PAPSActivitySelectionForm


# ================= PAPSSessionActivity 관리 API =================

@login_required
@teacher_required
@require_http_methods(["GET"])
def api_get_activity_form_fields(request):
    """
    선택된 학년에 따른 종목 선택 폼 필드 정보 반환
    GET /api/paps/session-activities/form-fields/?session_id=xxx&grades=4,5,6
    """
    try:
        session_id = request.GET.get('session_id')
        grades_str = request.GET.get('grades', '')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_id가 필요합니다.'
            })
        
        # 세션 권한 확인
        session = get_object_or_404(
            PAPSSession,
            id=session_id,
            teacher_id=request.user.teacher.id
        )
        
        if session.is_completed:
            return JsonResponse({
                'success': False,
                'error': '완료된 측정회차는 수정할 수 없습니다.'
            })
        
        # 학년 파싱
        try:
            selected_grades = [int(g.strip()) for g in grades_str.split(',') if g.strip()]
        except (ValueError, AttributeError):
            return JsonResponse({
                'success': False,
                'error': '올바른 학년을 선택해주세요.'
            })
        
        if not selected_grades:
            return JsonResponse({
                'success': False,
                'error': '최소 하나의 학년을 선택해주세요.'
            })
        
        # 카테고리별 활동 정보 구성
        required_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        ).order_by('order')
        
        optional_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.OPTIONAL
        ).order_by('order')
        
        # 기존 선택된 종목들 조회
        existing_activities = {}
        existing_selections = PAPSSessionActivity.objects.filter(
            session_id=session.id,
            grade__in=selected_grades
        )
        
        for selection in existing_selections:
            key = f"{selection.category_id}_{selection.grade}"
            existing_activities[key] = str(selection.activity_id)
        
        # 폼 필드 데이터 구성
        form_data = {
            'required_categories': [],
            'optional_categories': [],
            'existing_selections': existing_activities
        }
        
        # 필수평가 카테고리
        for category in required_categories:
            activities = PAPSActivity.objects.filter(category_id=category.id)
            category_data = {
                'id': str(category.id),
                'name': category.name,
                'display_name': category.get_name_display(),
                'activities': [
                    {
                        'id': str(activity.id),
                        'name': activity.name,
                        'display_name': activity.get_name_display()
                    }
                    for activity in activities
                ],
                'grades': []
            }
            
            # 각 학년별 폼 필드 정보
            for grade in selected_grades:
                field_name = f"required_{category.name}_{grade}"
                selected_activity = existing_activities.get(f"{category.id}_{grade}")
                
                category_data['grades'].append({
                    'grade': grade,
                    'field_name': field_name,
                    'selected_value': selected_activity,
                    'grade_display': get_grade_display(grade)
                })
            
            form_data['required_categories'].append(category_data)
        
        # 선택평가 카테고리 (있는 경우)
        for category in optional_categories:
            activities = PAPSActivity.objects.filter(category_id=category.id)
            category_data = {
                'id': str(category.id),
                'name': category.name,
                'display_name': category.get_name_display(),
                'activities': [
                    {
                        'id': str(activity.id),
                        'name': activity.name,
                        'display_name': activity.get_name_display()
                    }
                    for activity in activities
                ],
                'grades': []
            }
            
            # 각 학년별 폼 필드 정보
            for grade in selected_grades:
                field_name = f"optional_{category.name}_{grade}"
                selected_activity = existing_activities.get(f"{category.id}_{grade}")
                
                category_data['grades'].append({
                    'grade': grade,
                    'field_name': field_name,
                    'selected_value': selected_activity,
                    'grade_display': get_grade_display(grade)
                })
            
            form_data['optional_categories'].append(category_data)
        
        return JsonResponse({
            'success': True,
            'data': form_data,
            'selected_grades': selected_grades,
            'session': {
                'id': str(session.id),
                'name': session.name,
                'is_completed': session.is_completed
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'폼 필드 로드 중 오류: {str(e)}'
        })


@login_required
@teacher_required
@require_POST
@csrf_exempt
def api_save_session_activities(request):
    """
    선택된 종목들을 저장
    POST /api/paps/session-activities/save/
    """
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id')
        selected_grades = data.get('selected_grades', [])
        activity_selections = data.get('activity_selections', {})
        
        # 필수 파라미터 확인
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_id가 필요합니다.'
            })
        
        if not selected_grades:
            return JsonResponse({
                'success': False,
                'error': '선택된 학년이 없습니다.'
            })
        
        # 세션 권한 확인
        session = get_object_or_404(
            PAPSSession,
            id=session_id,
            teacher_id=request.user.teacher.id
        )
        
        if session.is_completed:
            return JsonResponse({
                'success': False,
                'error': '완료된 측정회차는 수정할 수 없습니다.'
            })
        
        # 필수평가 검증
        required_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        )
        
        missing_required = []
        for category in required_categories:
            for grade in selected_grades:
                field_name = f"required_{category.name}_{grade}"
                if not activity_selections.get(field_name):
                    grade_display = get_grade_display(grade)
                    missing_required.append(f"{grade_display} {category.get_name_display()}")
        
        if missing_required:
            return JsonResponse({
                'success': False,
                'error': f'다음 필수평가 영역을 선택해주세요: {", ".join(missing_required)}'
            })
        
        # 데이터베이스 저장
        with transaction.atomic():
            # 기존 선택 삭제
            PAPSSessionActivity.objects.filter(
                session_id=session.id,
                grade__in=selected_grades
            ).delete()
            
            # 새로운 선택 저장
            session_activities = []
            
            for field_name, activity_id in activity_selections.items():
                if not activity_id:  # 선택되지 않은 경우 건너뛰기
                    continue
                
                # 필드명 파싱: required_CARDIO_4, optional_BODY_FAT_6, optional_BODY_FAT_RATE_7 등
                parts = field_name.split('_')
                if len(parts) < 3:
                    continue
                
                try:
                    evaluation_type = parts[0]  # required 또는 optional
                    grade = int(parts[-1])      # 마지막 요소가 학년
                    category_name = '_'.join(parts[1:-1])  # 중간 부분들을 다시 결합
                except (ValueError, IndexError) as e:
                    print(f"필드명 파싱 오류: {field_name}, 에러: {e}")
                    continue
                
                try:
                    category = PAPSCategory.objects.get(name=category_name)
                    activity = PAPSActivity.objects.get(id=activity_id)
                    
                    session_activity = PAPSSessionActivity(
                        session_id=session.id,
                        grade=grade,
                        category_id=category.id,
                        activity_id=activity.id
                    )
                    session_activities.append(session_activity)
                    
                except PAPSCategory.DoesNotExist:
                    print(f"카테고리를 찾을 수 없음: {category_name}")
                    continue
                except PAPSActivity.DoesNotExist:
                    print(f"활동을 찾을 수 없음: {activity_id}")
                    continue
            
            # 벌크 생성
            PAPSSessionActivity.objects.bulk_create(session_activities)
            
            return JsonResponse({
                'success': True,
                'message': f'{len(selected_grades)}개 학년, {len(session_activities)}개 종목이 저장되었습니다.',
                'data': {
                    'saved_count': len(session_activities),
                    'grades_count': len(selected_grades)
                }
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON 데이터가 올바르지 않습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'저장 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_get_existing_activities(request):
    """
    특정 세션의 기존 선택된 종목들 조회
    GET /api/paps/session-activities/existing/?session_id=xxx
    """
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_id가 필요합니다.'
            })
        
        # 세션 권한 확인
        session = get_object_or_404(
            PAPSSession,
            id=session_id,
            teacher_id=request.user.teacher.id
        )
        
        # 기존 선택된 종목들 조회
        existing_activities = PAPSSessionActivity.objects.filter(
            session_id=session.id
        )
        
        activities_data = []
        for activity in existing_activities:
            activities_data.append({
                'grade': activity.grade,
                'grade_display': get_grade_display(activity.grade),
                'category_id': str(activity.category_id),
                'category_name': activity.category_id,  # 실제로는 category 객체에서 가져와야 함
                'activity_id': str(activity.activity_id),
                'activity_name': activity.activity_id,  # 실제로는 activity 객체에서 가져와야 함
            })
        
        return JsonResponse({
            'success': True,
            'data': activities_data,
            'total': len(activities_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'기존 종목 조회 중 오류: {str(e)}'
        })


# ================= 헬퍼 함수 =================

def get_grade_display(grade):
    """학년 숫자를 한글 표시로 변환"""
    if grade <= 6:
        return f"초등 {grade}학년"
    elif grade <= 9:
        return f"중학 {grade - 6}학년"
    else:
        return f"고등 {grade - 9}학년"