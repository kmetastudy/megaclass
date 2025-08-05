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
    PAPSActivity, PAPSRecord
)
from accounts.models import Student, Class
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
        
        # 기존 선택된 종목들 조회 (활성 상태인 것만)
        existing_activities = {}
        existing_selections = PAPSSessionActivity.objects.filter(
            session_id=session.id,
            grade__in=selected_grades,
            is_active=True
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
        print(f"Received data: session_id={session_id}, selected_grades={selected_grades}, activity_selections={activity_selections}")
        
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
        
        # 데이터베이스 저장 (Activate/Deactivate 패턴)
        with transaction.atomic():
            from .utils import create_default_paps_records, deactivate_session_activity
            
            # 모든 기존 항목들 조회 (활성/비활성 구분없이)
            all_existing_activities = PAPSSessionActivity.objects.filter(
                session_id=session.id,
                grade__in=selected_grades
            )
            
            # 기존 항목들을 활성/비활성 구분하여 매핑
            active_existing_map = {}  # category_id + grade -> 활성 항목
            inactive_existing_map = {}  # category_id + grade + activity_id -> 비활성 항목들
            
            for existing in all_existing_activities:
                category_grade_key = f"{existing.category_id}_{existing.grade}"
                category_grade_activity_key = f"{existing.category_id}_{existing.grade}_{existing.activity_id}"
                
                if existing.is_active:
                    active_existing_map[category_grade_key] = existing
                else:
                    inactive_existing_map[category_grade_activity_key] = existing
            
            # 새로운 선택들을 파싱하여 필요한 항목들 파악
            new_selections = {}
            activities_to_create = []
            
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
                    
                    key = f"{category.id}_{grade}"
                    new_selections[key] = {
                        'category': category,
                        'activity': activity,
                        'grade': grade
                    }
                    
                except PAPSCategory.DoesNotExist:
                    print(f"카테고리를 찾을 수 없음: {category_name}")
                    continue
                except PAPSActivity.DoesNotExist:
                    print(f"활동을 찾을 수 없음: {activity_id}")
                    continue
            
            # 1. 기존 활성 항목 중 선택이 변경되었거나 제거된 항목들을 비활성화
            deactivated_count = 0
            for key, existing_activity in active_existing_map.items():
                new_selection = new_selections.get(key)
                
                if not new_selection or str(new_selection['activity'].id) != str(existing_activity.activity_id):
                    # 선택이 변경되었거나 제거된 경우 비활성화
                    result = deactivate_session_activity(existing_activity)
                    if result['success']:
                        deactivated_count += 1
            
            # 2. 새로운 항목들이나 변경된 항목들을 위한 PAPSSessionActivity 생성/재활성화
            created_count = 0
            reactivated_count = 0
            
            for key, selection in new_selections.items():
                active_existing = active_existing_map.get(key)
                
                # 기존 활성 항목이 없거나, 있지만 선택된 활동이 다른 경우
                if not active_existing or str(selection['activity'].id) != str(active_existing.activity_id):
                    
                    # 우선 같은 activity_id를 가진 비활성 항목이 있는지 확인
                    inactive_key = f"{selection['category'].id}_{selection['grade']}_{selection['activity'].id}"
                    existing_inactive = inactive_existing_map.get(inactive_key)
                    
                    if existing_inactive:
                        # 비활성 항목 재활성화
                        existing_inactive.is_active = True
                        existing_inactive.save()
                        print(f"기존 비활성 항목 재활성화: session={session.id}, grade={selection['grade']}, category={selection['category'].get_name_display()}, activity={selection['activity'].get_name_display()}")
                        
                        # PAPSRecord 자동 생성 (필요한 경우)
                        record_result = create_default_paps_records(existing_inactive, request.user.teacher.id)
                        if record_result['success']:
                            print(f"PAPSRecord 자동 생성: {record_result['created_count']}개 생성, {record_result['skipped_count']}개 건너뛰기")
                        
                        activities_to_create.append(existing_inactive)
                        reactivated_count += 1
                    else:
                        # 새로운 PAPSSessionActivity 생성
                        try:
                            new_session_activity = PAPSSessionActivity.objects.create(
                                session_id=session.id,
                                grade=selection['grade'],
                                category_id=selection['category'].id,
                                activity_id=selection['activity'].id,
                                is_active=True
                            )
                            print(f"신규 PAPSSessionActivity 생성: session={session.id}, grade={selection['grade']}, category={selection['category'].get_name_display()}, activity={selection['activity'].get_name_display()}")
                            
                            # 새로운 세션 활동에 대한 PAPSRecord 자동 생성
                            record_result = create_default_paps_records(new_session_activity, request.user.teacher.id)
                            if record_result['success']:
                                print(f"PAPSRecord 자동 생성: {record_result['created_count']}개 생성, {record_result['skipped_count']}개 건너뛰기")
                            else:
                                print(f"PAPSRecord 생성 실패: {record_result['error']}")
                            
                            activities_to_create.append(new_session_activity)
                            created_count += 1
                            
                        except Exception as create_error:
                            print(f"PAPSSessionActivity 생성 실패: {create_error}")
                            raise create_error
            
            # 응답 메시지 구성
            total_selections = len(new_selections)
            message_parts = [f'{len(selected_grades)}개 학년']
            
            if created_count > 0:
                message_parts.append(f'{created_count}개 종목 신규생성')
            if reactivated_count > 0:
                message_parts.append(f'{reactivated_count}개 종목 재활성화')
            if deactivated_count > 0:
                message_parts.append(f'{deactivated_count}개 종목 비활성화')
            
            message = ', '.join(message_parts) + '되었습니다.'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'data': {
                    'total_selections': total_selections,
                    'created_count': created_count,
                    'reactivated_count': reactivated_count,
                    'deactivated_count': deactivated_count,
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
        
        # 기존 선택된 종목들 조회 (활성 상태인 것만)
        existing_activities = PAPSSessionActivity.objects.filter(
            session_id=session.id,
            is_active=True
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


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_get_session_activities(request):
    """
    선택된 세션과 학년에 대한 활성화된 PAPSSessionActivity 조회
    GET /api/paps/session-activities/?session_id=xxx&grade=6
    """
    try:
        session_id = request.GET.get('session_id')
        grade = request.GET.get('grade')
        
        if not session_id:
            return JsonResponse({
                'success': False, 
                'error': '측정회차 ID가 필요합니다.'
            })
        
        # 세션 확인 및 권한 검증
        try:
            session = PAPSSession.objects.get(
                id=session_id,
                teacher_id=request.user.teacher.id
            )
        except PAPSSession.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': '측정회차를 찾을 수 없습니다.'
            })
        
        # 활성화된 PAPSSessionActivity 조회
        query = PAPSSessionActivity.objects.filter(
            session_id=session_id,
            is_active=True
        )
        
        if grade:
            query = query.filter(grade=int(grade))
        
        # 관련 Activity와 Category 정보 조합
        activities_data = []
        for session_activity in query:
            try:
                activity = PAPSActivity.objects.get(id=session_activity.activity_id)
                category = PAPSCategory.objects.get(id=activity.category_id)
                
                activities_data.append({
                    'id': str(session_activity.id),
                    'activity_id': str(activity.id),
                    'name': activity.get_name_display(),
                    'category_name': category.get_name_display(),
                    'evaluation_type': category.evaluation_type,
                    'grade': session_activity.grade,
                    'grade_display': get_grade_display(session_activity.grade)
                })
            except (PAPSActivity.DoesNotExist, PAPSCategory.DoesNotExist):
                # 참조 무결성 오류 시 해당 항목 스킵
                continue
        
        return JsonResponse({
            'success': True,
            'activities': activities_data,
            'total': len(activities_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 조회 중 오류가 발생했습니다: {str(e)}'
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


# ================= 엑셀 Export API =================

@login_required
@teacher_required
@require_POST
def api_export_paps_records(request):
    """
    PAPS 측정 데이터를 엑셀 Export용으로 조회
    POST /api/paps/export-records/
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        activity_ids = data.get('activity_ids', [])
        grade = data.get('grade')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': '측정회차 ID가 필요합니다.'
            })
        
        if not activity_ids:
            return JsonResponse({
                'success': False,
                'error': '측정 항목을 선택해주세요.'
            })
        
        # 세션 확인 및 권한 검증
        try:
            session = PAPSSession.objects.get(
                id=session_id,
                teacher_id=request.user.teacher.id
            )
        except PAPSSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '측정회차를 찾을 수 없습니다.'
            })
        
        # activity_ids에 해당하는 PAPSActivity들을 DB 순서대로 조회
        activities = PAPSActivity.objects.filter(id__in=activity_ids).order_by('created_at')
        
        # 활동 정보 조회 및 컬럼 생성
        columns = []
        activities_info = {}
        
        for activity in activities:
            activity_id = str(activity.id)
            if activity_id not in activity_ids:
                continue
                
            activities_info[activity_id] = activity
            
            # measurement_schema에서 readonly=false인 필드들만 추출
            if activity.measurement_schema and 'fields' in activity.measurement_schema:
                for field in activity.measurement_schema['fields']:
                    if not field.get('readonly', False):
                        columns.append({
                            'name': field['name'],
                            'field': field['field'],
                            'activity_id': activity_id,
                            'activity_name': activity.name,
                            'type': field.get('type', 'text'),
                            'validation': {
                                'min': field.get('min'),
                                'max': field.get('max'),
                                'decimal_places': field.get('decimal_places')
                            }
                        })
        
        # 학생 목록 조회 (교사가 담당하는 학급의 해당 학년 학생들)
        from accounts.models import ClassTeacher
        
        teacher_classes = ClassTeacher.objects.filter(
            teacher_id=request.user.teacher.id
        ).select_related('class_instance')
        
        class_ids = []
        for ct in teacher_classes:
            if ct.class_instance.grade == grade:
                class_ids.append(ct.class_instance.id)
        
        students = Student.objects.filter(
            school_class_id__in=class_ids
        ).select_related('school_class').order_by('school_class_id', 'student_id')
        
        # PAPSRecord 조회
        records = PAPSRecord.objects.filter(
            session_id=session_id,
            activity_id__in=activity_ids,
            measured_by_teacher_id=request.user.teacher.id,
            student_grade=grade
        )
        
        # 데이터 구성
        records_data = []
        records_dict = {}
        
        # records를 dict로 변환 (student_id, activity_id를 키로)
        for record in records:
            key = f"{record.student_id}_{record.activity_id}"
            records_dict[key] = record
        
        for student in students:
            student_data = {
                'school_year': session.school_year,
                'grade_display': get_grade_display(grade),
                'class_name': f"{student.school_class.class_number}반",
                'student_number': student.student_id,
                'student_name': student.user.last_name + student.user.first_name,
                'student_id': student.id
            }
            
            # 각 측정값 추가
            for col in columns:
                key = f"{student.id}_{col['activity_id']}"
                if key in records_dict:
                    measurement_data = records_dict[key].measurement_data
                    student_data[col['field']] = measurement_data.get(col['field'], '')
                else:
                    student_data[col['field']] = ''
            
            records_data.append(student_data)
        
        return JsonResponse({
            'success': True,
            'session_name': session.name,
            'columns': columns,
            'records': records_data,
            'total_students': len(records_data),
            'total_columns': len(columns)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON 데이터가 올바르지 않습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 조회 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
@require_POST
def api_download_paps_template(request):
    """
    PAPS 측정 템플릿을 위한 스키마 정보 제공
    POST /api/paps/download-template/
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        activity_ids = data.get('activity_ids', [])
        grade = data.get('grade')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': '측정회차 ID가 필요합니다.'
            })
        
        if not activity_ids:
            return JsonResponse({
                'success': False,
                'error': '측정 항목을 선택해주세요.'
            })
        
        # 세션 확인 및 권한 검증
        try:
            session = PAPSSession.objects.get(
                id=session_id,
                teacher_id=request.user.teacher.id
            )
        except PAPSSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '측정회차를 찾을 수 없습니다.'
            })
        
        # activity_ids에 해당하는 PAPSActivity들을 DB 순서대로 조회
        activities = PAPSActivity.objects.filter(id__in=activity_ids).order_by('created_at')
        
        # 활동 정보 조회 및 컬럼 생성 (Export와 동일한 로직)
        columns = []
        
        for activity in activities:
            activity_id = str(activity.id)
            if activity_id not in activity_ids:
                continue
            
            # measurement_schema에서 readonly=false인 필드들만 추출
            if activity.measurement_schema and 'fields' in activity.measurement_schema:
                for field in activity.measurement_schema['fields']:
                    if not field.get('readonly', False):
                        columns.append({
                            'name': field['name'],
                            'field': field['field'],
                            'activity_id': activity_id,
                            'activity_name': activity.name,
                            'type': field.get('type', 'text'),
                            'validation': {
                                'min': field.get('min'),
                                'max': field.get('max'),
                                'decimal_places': field.get('decimal_places')
                            }
                        })
        
        # 학생 목록 조회 (빈 템플릿용)
        from accounts.models import ClassTeacher
        
        teacher_classes = ClassTeacher.objects.filter(
            teacher_id=request.user.teacher.id
        ).select_related('class_instance')
        
        class_ids = []
        for ct in teacher_classes:
            if ct.class_instance.grade == grade:
                class_ids.append(ct.class_instance.id)
        
        students = Student.objects.filter(
            school_class_id__in=class_ids
        ).select_related('school_class').order_by('school_class_id', 'student_id')
        
        # 학생 기본 정보만 포함 (측정값은 빈값)
        students_data = []
        for student in students:
            student_data = {
                'school_year': session.school_year,
                'grade_display': get_grade_display(grade),
                'class_name': f"{student.school_class.class_number}반",
                'student_number': student.student_id,
                'student_name': student.user.last_name + student.user.first_name,
                'student_id': student.id
            }
            students_data.append(student_data)
        
        return JsonResponse({
            'success': True,
            'session_name': session.name,
            'columns': columns,
            'students': students_data,
            'total_students': len(students_data),
            'total_columns': len(columns)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON 데이터가 올바르지 않습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'템플릿 생성 중 오류가 발생했습니다: {str(e)}'
        })