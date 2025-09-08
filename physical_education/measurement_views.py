"""
PAPS 측정 관련 뷰 모듈
측정 화면 동적 로드 및 관련 기능을 담당
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from teacher.decorators import teacher_required
from .models import (
    PAPSSession,
    PAPSActivity,
    PAPSRecord,
    PAPSCategory,
)
from .excel_utils import create_paps_excel_workbook, prepare_demo_data_for_excel
from accounts.models import ClassTeacher, Class, Student
from .views import get_student_gender, get_student_number_from_id
from .utils import get_korean_name, calculate_paps_grade, process_measurement_data, DemoSessionManager
import json
import logging

logger = logging.getLogger(__name__)

# 종목별 템플릿 매핑
ACTIVITY_TEMPLATE_MAP = {
    'SHUTTLE_RUN': 'shuttle_run.html',
    'LONG_RUN_WALK': 'long_run_walk.html',
    'STEP_TEST': 'step_test.html',
    'SIT_REACH': 'sit_reach.html',
    'COMPREHENSIVE_FLEXIBILITY': 'comprehensive_flexibility.html',
    'PUSH_UP': 'push_up.html',
    'SIT_UP': 'sit_up.html',
    'GRIP_STRENGTH': 'grip_strength.html',
    'FIFTY_METER_RUN': 'fifty_meter_run.html',
    'STANDING_LONG_JUMP': 'standing_long_jump.html',
    'BMI': 'bmi.html',
    # 선택평가 종목들 (나중에 추가)
    'CARDIO_PRECISION_TEST': 'cardio_precision_test.html',
    'BODY_FAT_RATE_TEST': 'body_fat_rate_test.html',
    'POSTURE_TEST': 'posture_test.html',
    'SELF_BODY_TEST': 'self_body_test.html',
}

@login_required
@teacher_required
def paps_measure_activity_view(request, activity_id):
    """PAPS 측정 화면 - 종목별 (2단계) 뷰"""
    teacher_id = request.user.teacher.id
    
    # URL 파라미터에서 필요 정보 추출
    school_year = request.GET.get('school_year')
    session_id = request.GET.get('session_id')
    grade = request.GET.get('grade')
    class_id = request.GET.get('class_id')
    print(f"Activity ID: {activity_id}, School Year: {school_year}, Session ID: {session_id}, Grade: {grade}, Class ID: {class_id}")
    
    # 1. 파라미터 검증
    if not all([school_year, session_id, grade, class_id]):
        messages.error(request, '필수 파라미터가 누락되었습니다.')
        return redirect('physical_education:paps_measure')
    
    try:
        # 2. 권한 확인 및 데이터 조회
        # Activity 정보 조회
        activity = get_object_or_404(PAPSActivity, id=activity_id)
        
        # Session 권한 확인
        session = get_object_or_404(
            PAPSSession, 
            id=session_id, 
            teacher_id=teacher_id
        )
        
        # Class 정보 및 권한 확인
        class_instance = get_object_or_404(Class, id=class_id, grade=int(grade))
        
        # 교사가 해당 학급을 담당하는지 확인
        if not ClassTeacher.objects.filter(
            teacher_id=teacher_id, 
            class_instance=class_instance
        ).exists():
            messages.error(request, '해당 학급에 대한 권한이 없습니다.')
            return redirect('physical_education:paps_measure')
        
        # 3. 학생 목록 조회
        students = Student.objects.filter(
            school_class=class_instance
        ).select_related('user').order_by('student_id')
        
        # 4. 기존 측정 기록 조회
        existing_records = PAPSRecord.objects.filter(
            session_id=session_id,
            activity_id=activity_id,
            student_id__in=[s.id for s in students]
        )
        
        # 학생별 기록 매핑
        records_by_student = {
            record.student_id: record 
            for record in existing_records
        }
        
        # 5. 학생 데이터와 측정 기록 결합
        students_data = []
        for student in students:
            record = records_by_student.get(student.id)
            
            student_data = {
                'id': student.id,
                'name': get_korean_name(student.user),
                'number': get_student_number_from_id(student.student_id),
                'gender': get_student_gender(student),
                'student_id': student.student_id,
                'birth_date': (
                    student.birth_date.strftime('%Y-%m-%d') 
                    if student.birth_date else None
                ),
                # 기존 측정 기록
                'measurement_data': record.measurement_data if record else {},
                'evaluation_grade': record.evaluation_grade if record else None,
                'measured_at': (
                    record.measured_at.isoformat() 
                    if record and record.measured_at else None
                ),
                'notes': record.notes if record else '',
                'record_id': str(record.id) if record else None,
                'record': record  # 템플릿에서 사용
            }
            students_data.append(student_data)
        
        # 6. 종목별 템플릿 선택
        template_name = ACTIVITY_TEMPLATE_MAP.get(
            activity.name, 
            'default_measurement.html'
        )
        
        activity_template = f'physical_education/teachers/paps/measurement/activities/{template_name}'
        
        # 7. 통계 계산
        total_students = len(students_data)
        measured_students = len([s for s in students_data if s['record_id']])
        
        # JavaScript용 JSON 데이터 준비 (record 객체 제외)
        students_data_for_json = []
        for student_data in students_data:
            json_safe_data = {k: v for k, v in student_data.items() if k != 'record'}
            students_data_for_json.append(json_safe_data)
        
        # 8. 컨텍스트 구성
        context = {
            # 기본 정보
            'session': session,
            'activity': activity,
            'class_info': class_instance,
            'students': students_data,
            'activity_template': activity_template,
            
            # 파라미터
            'school_year': int(school_year),
            'grade': int(grade),
            'class_id': int(class_id),
            'session_id': session_id,
            'activity_id': activity_id,
            
            # 통계
            'total_students': total_students,
            'measured_students': measured_students,
            
            # 측정 스키마 (필요시)
            'measurement_schema': activity.measurement_schema,
            
            # JavaScript에서 필요한 JSON 데이터
            'students_json': json.dumps(students_data_for_json, ensure_ascii=False),
            'evaluation_criteria_json': json.dumps(activity.evaluation_criteria, ensure_ascii=False) if activity.evaluation_criteria else 'null',
        }
        
        return render(
            request, 
            'physical_education/teachers/paps/measurement/measure_activity.html', 
            context
        )
        
    except Exception as e:
        print(f"Error in paps_measure_activity_view: {str(e)}")
        messages.error(request, f'측정 화면을 불러오는 중 오류가 발생했습니다: {str(e)}')
        return redirect('physical_education:paps_measure')


# ==================== PAPS 체험하기 기능 ====================

def demo_measurement_view(request):
    """PAPS 측정 체험하기 메인 페이지"""
    try:
        # 필수평가 종목 11개만 조회 (캐시 적용)
        cache_key = 'paps_required_activities'
        required_activities = cache.get(cache_key)
        
        if required_activities is None:
            required_activities = list(PAPSActivity.objects.filter(
                category_id__in=PAPSCategory.objects.filter(
                    evaluation_type=PAPSCategory.REQUIRED
                ).values_list('id', flat=True)
            ).order_by('name'))
            cache.set(cache_key, required_activities, 3600)  # 1시간 캐시

        # 가상 학생 데이터 생성
        demo_students = DemoSessionManager.get_demo_students()

        # 세션에서 선택된 종목 확인
        selected_activity_name = DemoSessionManager.get_selected_activity(request)
        
        if selected_activity_name and required_activities:
            # 해당 종목이 실제로 존재하는지 확인
            default_activity = next(
                (act for act in required_activities if act.name == selected_activity_name),
                required_activities[0]
            )
        else:
            default_activity = required_activities[0] if required_activities else None

        context = {
            'is_demo': True,
            'activities': required_activities,
            'students': demo_students,
            'default_activity': default_activity,
        }

        return render(request, 'physical_education/paps/demo/measurement/measurement.html', context)
        
    except Exception as e:
        logger.error(f"체험 페이지 로드 실패: {str(e)}")
        return render(request, 'physical_education/paps/demo/measurement/error.html', {
            'error_message': '페이지를 불러오는 중 오류가 발생했습니다.'
        })

def demo_activity_view(request):
    """종목별 측정 화면 동적 로드 - 기존 템플릿 재사용"""
    activity_name = request.GET.get('activity', '').strip()
    
    if not activity_name:
        return HttpResponse("종목을 선택해주세요.", status=400)

    try:
        activity = get_object_or_404(PAPSActivity, name=activity_name)
        
        # 선택한 종목을 세션에 저장
        DemoSessionManager.save_selected_activity(request, activity_name)
        
        # 기존 종목별 템플릿 그대로 사용
        activity_template = f'physical_education/teachers/paps/measurement/activities/{activity_name.lower()}.html'
        
        # 가상 학생 데이터
        demo_students = DemoSessionManager.get_demo_students()
        
        # 학생 데이터에 기존 측정 결과 추가 (PAPSRecord 구조 활용)
        for student in demo_students:
            student_id = student['id']
            existing_record = DemoSessionManager.get_student_record(request, student_id, activity_name)
            
            if existing_record:
                student['measurement_data'] = existing_record['measurement_data']
                student['evaluation_grade'] = existing_record['evaluation_grade']
                student['record'] = True
            else:
                student['measurement_data'] = {}
                student['evaluation_grade'] = None
                student['record'] = False

        # JavaScript용 JSON 데이터 준비 (paps_measure_activity_view와 동일하게)
        students_data_for_json = []
        for student_data in demo_students:
            json_safe_data = {k: v for k, v in student_data.items()}
            students_data_for_json.append(json_safe_data)

        context = {
            'is_demo': True,  # 체험 모드 플래그
            'activity': activity,
            'students': demo_students,
            'school_year': 2025,
            'grade': 4,  # 초4 고정
            'total_students': len(demo_students),
            'measured_students': sum(1 for s in demo_students if s['record']),
            'class_info': {'grade': '초4', 'class_number': '체험'},
            # 체험 모드에서는 세션 관련 정보를 가짜로 제공
            'session': {'id': 'demo', 'name': '체험 모드'},
            'session_id': 'demo',
            'activity_id': str(activity.id),
            'class_id': 1,  # 숫자로 변경 (JavaScript 에러 방지)
            'csrf_token': '',  # 빈 문자열이라도 제공
            # JavaScript에서 필요한 JSON 데이터
            'students_json': json.dumps(students_data_for_json, ensure_ascii=False),
            'evaluation_criteria_json': json.dumps(activity.evaluation_criteria, ensure_ascii=False) if activity.evaluation_criteria else 'null',
        }

        return render(request, activity_template, context)

    except PAPSActivity.DoesNotExist:
        return HttpResponse("존재하지 않는 종목입니다.", status=404)
    except Exception as e:
        logger.error(f"종목 로드 실패 ({activity_name}): {str(e)}")
        return HttpResponse("종목을 불러오는 중 오류가 발생했습니다.", status=500)

@csrf_exempt  # 체험 모드는 CSRF 제외
@transaction.atomic  # 동시성 이슈 방지
def demo_save_measurement(request):
    """체험 모드 측정 데이터 저장 API - 실제 API와 동일한 구조"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        data = json.loads(request.body)
        
        student_id = data.get('student_id')
        activity_id = data.get('activity_id')
        measurement_data = data.get('measurement_data', {})
        print(f"Received demo save request: student_id={student_id}, activity_id={activity_id}, data={measurement_data}")
        
        # 필수 파라미터 검증
        if not all([student_id, activity_id]):
            return JsonResponse({
                'success': False, 
                'error': '필수 파라미터가 누락되었습니다.'
            })
        
        # 학생 성별 정보 가져오기 (체험 모드는 가상 학생 데이터에서)
        demo_students = DemoSessionManager.get_demo_students()
        student = next((s for s in demo_students if s['id'] == int(student_id)), None)
        student_gender = student['gender'] if student else 'M'  # 기본값 M
        print(f"Student gender: {student_gender}")
        
        # 활동 정보 조회
        activity = get_object_or_404(PAPSActivity, id=activity_id)
        
        # 입력값 검증 및 처리 (기존 utils.py 함수 재사용)
        processed_data = process_measurement_data(activity.name, measurement_data, 4)  # 초4 고정
        
        # 등급 계산 (기존 utils.py 함수 재사용)
        print(f"processed_data: {processed_data}")
        grade_result = calculate_paps_grade(activity, processed_data, 4)
        print(f"Grade result: {grade_result}")
        
        # 성별에 따른 등급 추출
        evaluation_grade = None
        if grade_result and 'error' not in grade_result:
            # 학생 성별에 따라 적절한 등급 선택
            if student_gender == 'F':
                grade_code = grade_result.get('female_grade_code')
            else:
                grade_code = grade_result.get('male_grade_code')
            
            # grade_code가 'grade_1', 'grade_2' 등의 형태일 때 숫자만 추출
            if grade_code and grade_code.startswith('grade_'):
                try:
                    evaluation_grade = int(grade_code.split('_')[1])
                except (IndexError, ValueError):
                    pass
                    
        print(f"Evaluation grade extracted: {evaluation_grade}")
        # 세션에 저장 (PAPSRecord 구조와 동일)
        DemoSessionManager.save_record(
            request, 
            student_id, 
            activity.name,
            activity_id,
            processed_data,
            evaluation_grade
        )
        
        return JsonResponse({
            'success': True,
            'message': '측정 데이터가 저장되었습니다.',
            'evaluation_grade': evaluation_grade,
            'processed_data': processed_data
        })
        
    except Exception as e:
        logger.error(f"체험 모드 측정 저장 실패: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': '측정 데이터 저장 중 오류가 발생했습니다.'
        })


def demo_export_excel(request):
    """
    체험판 PAPS 측정 데이터를 Excel 파일로 export
    GET /demo/api/export-excel/
    """
    try:
        # 체험판 데이터 준비
        headers, rows = prepare_demo_data_for_excel(request)
        
        # 데이터가 없는 경우 처리
        if not rows:
            return JsonResponse({
                'success': False,
                'error': '체험 데이터가 없습니다. 먼저 측정을 체험해 보세요.'
            })
        
        # 파일명 생성 (현재 날짜 포함)
        current_date = timezone.now().strftime("%Y%m%d")
        filename = f"PAPS_체험판_측정데이터_{current_date}.xlsx"
        
        # Excel 파일 생성 및 다운로드
        return create_paps_excel_workbook(headers, rows, filename)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"체험판 Excel export 실패: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'error': f'Excel 파일 생성 중 오류가 발생했습니다: {str(e)}'
        })