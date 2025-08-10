"""
PAPS 측정 관련 뷰 모듈
측정 화면 동적 로드 및 관련 기능을 담당
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from teacher.decorators import teacher_required
from .models import (
    PAPSSession,
    PAPSSessionActivity,
    PAPSCategory,
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
@require_http_methods(["GET"])
def paps_load_measurement_view(request):
    """PAPS 측정 화면 동적 로드 뷰 (HTMX용)"""
    try:
        teacher_id = request.user.teacher.id
        
        # 파라미터 수집
        school_year = request.GET.get('school_year')
        session_id = request.GET.get('session_id') 
        grade = request.GET.get('grade')
        class_id = request.GET.get('class_id')
        activity_id = request.GET.get('activity_id')
        
        # 1. 파라미터 검증
        if not all([school_year, session_id, grade, class_id, activity_id]):
            return HttpResponse(
                '<div class="border-2 border-red-300 bg-red-50 rounded-lg p-8 text-center">'
                '<div class="text-red-600">'
                '<i class="fas fa-exclamation-triangle text-4xl mb-4"></i>'
                '<h3 class="text-lg font-medium mb-2">파라미터 오류</h3>'
                '<p class="text-sm">필수 파라미터가 누락되었습니다.</p>'
                '</div></div>',
                status=400
            )
        
        # 2. 권한 확인 - Session 소유권
        try:
            session = get_object_or_404(
                PAPSSession, 
                id=session_id, 
                teacher_id=teacher_id
            )
        except:
            return HttpResponse(
                '<div class="border-2 border-red-300 bg-red-50 rounded-lg p-8 text-center">'
                '<div class="text-red-600">'
                '<i class="fas fa-lock text-4xl mb-4"></i>'
                '<h3 class="text-lg font-medium mb-2">권한 오류</h3>'
                '<p class="text-sm">해당 측정회차에 대한 권한이 없습니다.</p>'
                '</div></div>',
                status=403
            )
        
        # 3. Activity 정보 조회
        try:
            activity = get_object_or_404(PAPSActivity, id=activity_id)
        except:
            return HttpResponse(
                '<div class="border-2 border-red-300 bg-red-50 rounded-lg p-8 text-center">'
                '<div class="text-red-600">'
                '<i class="fas fa-question-circle text-4xl mb-4"></i>'
                '<h3 class="text-lg font-medium mb-2">종목 오류</h3>'
                '<p class="text-sm">해당 측정 종목을 찾을 수 없습니다.</p>'
                '</div></div>',
                status=404
            )
        
        # 4. Class 정보 조회 및 권한 확인
        try:
            class_instance = Class.objects.get(id=class_id, grade=int(grade))
            
            # 교사가 해당 학급을 담당하는지 확인
            if not ClassTeacher.objects.filter(
                teacher_id=teacher_id, 
                class_instance=class_instance
            ).exists():
                return HttpResponse(
                    '<div class="border-2 border-red-300 bg-red-50 rounded-lg p-8 text-center">'
                    '<div class="text-red-600">'
                    '<i class="fas fa-ban text-4xl mb-4"></i>'
                    '<h3 class="text-lg font-medium mb-2">학급 권한 오류</h3>'
                    '<p class="text-sm">해당 학급에 대한 권한이 없습니다.</p>'
                    '</div></div>',
                    status=403
                )
                
        except Class.DoesNotExist:
            return HttpResponse(
                '<div class="border-2 border-red-300 bg-red-50 rounded-lg p-8 text-center">'
                '<div class="text-red-600">'
                '<i class="fas fa-search text-4xl mb-4"></i>'
                '<h3 class="text-lg font-medium mb-2">학급 오류</h3>'
                '<p class="text-sm">해당 학급을 찾을 수 없습니다.</p>'
                '</div></div>',
                status=404
            )
        
        # 5. 학생 목록 조회
        students = Student.objects.filter(
            school_class=class_instance
        ).select_related('user').order_by('student_id')
        
        # 6. 기존 측정 기록 조회
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
        
        # 7. 학생 데이터와 측정 기록 결합
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
        
        # 8. 템플릿 선택
        template_name = ACTIVITY_TEMPLATE_MAP.get(
            activity.name, 
            'default_measurement.html'  # 기본 템플릿
        )
        
        template_path = f'physical_education/teachers/paps/measurement/activities/{template_name}'
        
        # 9. 컨텍스트 구성
        context = {
            # 기본 정보
            'session': session,
            'activity': activity,
            'class_info': class_instance,
            'students': students_data,
            
            # 파라미터
            'school_year': int(school_year),
            'grade': int(grade),
            'class_id': int(class_id),
            'session_id': session_id,
            'activity_id': activity_id,
            
            # 추가 정보
            'total_students': len(students_data),
            'measured_students': len([s for s in students_data if s['record']]),
            
            # JSON 데이터 (JavaScript용)
            'students_json': json.dumps(students_data, default=str),
            'measurement_schema_json': json.dumps(activity.measurement_schema),
            'evaluation_criteria_json': json.dumps(activity.evaluation_criteria),
        }

        # 10. 템플릿 렌더링
        try:
            return render(request, template_path, context)
        except Exception as template_error:
            # 템플릿이 없으면 기본 에러 메시지
            return HttpResponse(
                f'<div class="border-2 border-yellow-300 bg-yellow-50 rounded-lg p-8 text-center">'
                f'<div class="text-yellow-700">'
                f'<i class="fas fa-exclamation-triangle text-4xl mb-4"></i>'
                f'<h3 class="text-lg font-medium mb-2">템플릿 준비 중</h3>'
                f'<p class="text-sm">{activity.get_name_display()} 측정 화면을 준비 중입니다.</p>'
                f'<p class="text-xs mt-2 text-gray-600">템플릿: {template_name}</p>'
                f'</div></div>',
                status=200
            )
            
    except Exception as e:
        # 예상하지 못한 오류
        return HttpResponse(
            f'<div class="border-2 border-red-300 bg-red-50 rounded-lg p-8 text-center">'
            f'<div class="text-red-600">'
            f'<i class="fas fa-bug text-4xl mb-4"></i>'
            f'<h3 class="text-lg font-medium mb-2">시스템 오류</h3>'
            f'<p class="text-sm">예상하지 못한 오류가 발생했습니다.</p>'
            f'<p class="text-xs mt-2 text-gray-500">오류: {str(e)}</p>'
            f'</div></div>',
            status=500
        )