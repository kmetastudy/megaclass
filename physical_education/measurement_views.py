"""
PAPS 측정 관련 뷰 모듈
측정 화면 동적 로드 및 관련 기능을 담당
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from teacher.decorators import teacher_required
from .models import (
    PAPSSession,
    PAPSActivity,
    PAPSRecord,
)
from accounts.models import ClassTeacher, Class, Student
from .views import get_student_gender, get_student_number_from_id
from .utils import get_korean_name
import json

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