"""
PAPS (Physical Activity Promotion System) 핵심 로직 구현

이 모듈은 PAPS 시스템의 핵심 계산 로직을 담당합니다:
1. 등급 계산 (evaluation_criteria 기반)
2. 자동 값 계산 (PEI, BMI, 최고값 등)
3. 성별/나이 처리
"""

import math
from decimal import Decimal, ROUND_UP
from typing import Dict, Any, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import PAPSActivity


# ==================== 유틸리티 함수 ====================

def get_grade_from_number(grade_number: int) -> str:
    """학년 숫자를 한글 학년으로 변환"""
    grade_mapping = {
        4: "초4", 5: "초5", 6: "초6",
        7: "중1", 8: "중2", 9: "중3", 
        10: "고1", 11: "고2", 12: "고3"
    }
    return grade_mapping.get(grade_number, f"학년{grade_number}")


def get_age_from_grade(grade_number: int) -> int:
    """학년에서 나이 계산 (대략적)"""
    return grade_number + 6


def safe_decimal(value: Union[str, int, float, Decimal]) -> Decimal:
    """안전한 Decimal 변환"""
    if value is None:
        return Decimal('0')
    return Decimal(str(value))


def safe_float(value: Union[str, int, float, Decimal]) -> float:
    """안전한 float 변환"""
    if value is None:
        return 0.0
    return float(value)


# ==================== 자동 값 계산 함수 ====================

def calculate_bmi(height_cm: Union[float, Decimal], weight_kg: Union[float, Decimal]) -> Decimal:
    """
    BMI 계산
    BMI(kg/m²) = 체중(kg) ÷ [신장(m) × 신장(m)]
    0.01kg/m² 단위에서 올림하여 0.1kg/m² 단위로 기록
    """
    height_cm = safe_decimal(height_cm)
    weight_kg = safe_decimal(weight_kg)
    
    if height_cm <= 0:
        return Decimal('0.0')
    
    height_m = height_cm / Decimal('100')
    bmi_raw = weight_kg / (height_m * height_m)
    
    # 0.01 단위에서 올림하여 0.1 단위로 반환
    bmi_rounded = (bmi_raw * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_UP) / Decimal('100')
    return bmi_rounded.quantize(Decimal('0.1'))


def calculate_pei(
    heart_rate_1: int, 
    heart_rate_2: int, 
    heart_rate_3: int,
    duration_seconds: int = 300,
    is_male_high_school: bool = False
) -> Decimal:
    """
    PEI (Physical Efficiency Index) 계산
    
    Args:
        heart_rate_1, 2, 3: 1분~1분30초, 2분~2분30초, 3분~3분30초 심박수
        duration_seconds: 스텝운동 지속시간 (기본 300초 = 5분)
        is_male_high_school: 고등학생 남자 여부
    """
    D = duration_seconds
    
    if is_male_high_school:
        # 고등학생(남): PEI = D × 100 / {5.5 × p} + {0.22 × (300-D)}
        # p: 1회 심박수만 사용
        p = heart_rate_1
        if p <= 0:
            return Decimal('0.0')
        pei = (D * 100) / (5.5 * p + 0.22 * (300 - D))
    else:
        # 초등학생, 중학생, 고등학생(여): PEI = D / (2 × P) × 100
        # P: 1회 + 2회 + 3회 심박수 합
        P = heart_rate_1 + heart_rate_2 + heart_rate_3
        if P <= 0:
            return Decimal('0.0')
        pei = (D / (2 * P)) * 100
    
    # 0.01 단위에서 올림하여 0.1 단위로 반환
    pei_decimal = Decimal(str(pei))
    return (pei_decimal * Decimal('10')).quantize(Decimal('1'), rounding=ROUND_UP) / Decimal('10')


def calculate_max_value(*values) -> Union[Decimal, float]:
    """여러 값 중 최댓값 계산 (악력, 앉아윗몸앞으로굽히기, 제자리멀리뛰기)"""
    valid_values = [safe_decimal(v) for v in values if v is not None]
    return max(valid_values) if valid_values else Decimal('0')


def calculate_total_score(*boolean_values) -> int:
    """여러 불린 값의 합계 (종합유연성: 성공=1, 실패=0)"""
    return sum(1 for v in boolean_values if v is True)


def calculate_exercise_intensity(avg_heart_rate: int, age: int) -> int:
    """
    운동강도 계산 (심폐지구력정밀평가)
    
    1단계: 기본 비율 계산 = 평균 심박수 ÷ (220 - 나이)
    2단계: 소수점 3자리에서 올림처리
    3단계: 백분율 변환
    """
    if age <= 0 or avg_heart_rate <= 0:
        return 0
    
    # 1단계: 기본 비율 계산
    ratio = avg_heart_rate / (220 - age)
    
    # 2단계: 소수점 3자리에서 올림 (소수점 2자리까지)
    ratio_rounded = math.ceil(ratio * 100) / 100
    
    # 3단계: 백분율 변환
    intensity = int(ratio_rounded * 100)
    
    return min(intensity, 100)  # 최대 100%




# ==================== 등급 계산 함수 ====================

def calculate_grade(
    measurement_value: Union[float, Decimal],
    evaluation_criteria: Dict[str, Any],
    student_grade: int,
    gender: str = None
) -> Dict[str, Any]:
    """
    측정값을 기반으로 PAPS 등급 계산
    
    Args:
        measurement_value: 측정값
        evaluation_criteria: 평가 기준 데이터
        student_grade: 학생 학년 (4-12)
        gender: 성별 ('male' 또는 'female', None이면 둘 다 계산)
    
    Returns:
        {
            'male_grade': '1등급' 또는 '마름' 등,
            'female_grade': '1등급' 또는 '마름' 등,
            'male_grade_code': 'grade_1' 또는 'underweight' 등,
            'female_grade_code': 'grade_1' 또는 'underweight' 등,
            'error': 에러 메시지 (있을 경우)
        }
    """
    if not evaluation_criteria:
        return {'error': '평가 기준이 없습니다'}
    
    measurement_value = safe_decimal(measurement_value)
    grade_str = get_grade_from_number(student_grade)
    
    gender_specific = evaluation_criteria.get('gender_specific', False)
    criteria = evaluation_criteria.get('criteria', {})
    grade_labels = evaluation_criteria.get('grade_labels', {})
    calculation_method = evaluation_criteria.get('calculation_method', 'higher_better')
    
    result = {}
    
    # 성별별 등급 계산
    genders_to_check = ['male', 'female'] if gender is None else [gender]
    
    for check_gender in genders_to_check:
        grade_code = None
        grade_label = None
        
        if gender_specific:
            gender_criteria = criteria.get(check_gender, {})
        else:
            gender_criteria = criteria.get('all', {})
        
        # 학년별 기준이 있는지 확인
        if grade_str in gender_criteria:
            grade_criteria = gender_criteria[grade_str]
        elif 'all_grades' in gender_criteria:
            grade_criteria = gender_criteria['all_grades']
        else:
            result[f'{check_gender}_grade'] = None
            result[f'{check_gender}_grade_code'] = None
            continue
        
        # 등급 결정
        for grade_key, range_info in grade_criteria.items():
            min_val = range_info.get('min')
            max_val = range_info.get('max')
            
            # 범위 체크
            in_range = True
            
            if calculation_method == 'lower_better':
                # 값이 낮을수록 좋음 (시간 등)
                if min_val is not None and measurement_value < min_val:
                    in_range = False
                if max_val is not None and measurement_value > max_val:
                    in_range = False
            else:
                # 값이 높을수록 좋음 (기본)
                if min_val is not None and measurement_value < min_val:
                    in_range = False
                if max_val is not None and measurement_value > max_val:
                    in_range = False
            
            if in_range:
                grade_code = grade_key
                grade_label = grade_labels.get(grade_key, grade_key)
                break
        
        result[f'{check_gender}_grade'] = grade_label
        result[f'{check_gender}_grade_code'] = grade_code
    
    return result


# ==================== 측정 데이터 처리 함수 ====================

def process_measurement_data(
    activity_name: str,
    measurement_data: Dict[str, Any],
    student_grade: int
) -> Dict[str, Any]:
    """
    측정 데이터 처리 및 자동 계산 수행
    
    Args:
        activity_name: 종목명 (예: 'SHUTTLE_RUN')
        measurement_data: 입력된 측정 데이터
        student_grade: 학생 학년
    
    Returns:
        처리된 측정 데이터 (자동 계산 값 포함)
    """
    processed_data = measurement_data.copy()
    
    # 종목별 자동 계산 로직
    if activity_name == 'BMI':
        # BMI 계산
        height = measurement_data.get('height')
        weight = measurement_data.get('weight')
        if height and weight:
            processed_data['bmi'] = float(calculate_bmi(height, weight))
    
    elif activity_name == 'STEP_TEST':
        # PEI 계산
        hr1 = measurement_data.get('heart_rate_1')
        hr2 = measurement_data.get('heart_rate_2')
        hr3 = measurement_data.get('heart_rate_3')
        if all([hr1, hr2, hr3]):
            # TODO: 성별 정보가 없어 임시로 학년만으로 고등학교 남학생 판단
            # 향후 성별 정보 추가 시 수정 필요 (고등학교 남학생만 다른 PEI 계산 공식 사용)
            is_male_hs = student_grade >= 10  # 임시로 고등학교 남학생 판단
            processed_data['pei'] = float(calculate_pei(hr1, hr2, hr3, is_male_high_school=is_male_hs))
    
    elif activity_name == 'GRIP_STRENGTH':
        # 악력 최댓값 계산
        values = [
            measurement_data.get('right_first'),
            measurement_data.get('left_first'),
            measurement_data.get('right_second'),
            measurement_data.get('left_second')
        ]
        if any(v is not None for v in values):
            processed_data['best_grip'] = float(calculate_max_value(*values))
    
    elif activity_name == 'SIT_REACH':
        # 앉아윗몸앞으로굽히기 최댓값
        first = measurement_data.get('first_attempt')
        second = measurement_data.get('second_attempt')
        if first is not None and second is not None:
            processed_data['best_record'] = float(calculate_max_value(first, second))
    
    elif activity_name == 'STANDING_LONG_JUMP':
        # 제자리멀리뛰기 최댓값
        first = measurement_data.get('first_attempt')
        second = measurement_data.get('second_attempt')
        if first is not None and second is not None:
            processed_data['best_record'] = float(calculate_max_value(first, second))
    
    elif activity_name == 'COMPREHENSIVE_FLEXIBILITY':
        # 종합유연성 총점
        boolean_fields = [
            'shoulder_left', 'shoulder_right', 'body_left', 'body_right',
            'side_left', 'side_right', 'lower_body_left', 'lower_body_right'
        ]
        values = [measurement_data.get(field, False) for field in boolean_fields]
        processed_data['total_score'] = calculate_total_score(*values)
    
    
    elif activity_name == 'CARDIO_PRECISION_TEST':
        # 심폐지구력정밀평가 운동강도 계산
        avg_hr = measurement_data.get('avg_heart_rate')
        if avg_hr:
            age = get_age_from_grade(student_grade)
            processed_data['avg_intensity'] = calculate_exercise_intensity(avg_hr, age)
    
    elif activity_name == 'BODY_FAT_RATE_TEST':
        # 체지방률평가 BMI 계산
        height = measurement_data.get('height')
        weight = measurement_data.get('weight')
        if height and weight:
            processed_data['bmi'] = float(calculate_bmi(height, weight))
    
    return processed_data


def calculate_paps_grade(
    activity: 'PAPSActivity',
    measurement_data: Dict[str, Any],
    student_grade: int
) -> Dict[str, Any]:
    """
    PAPS 등급 계산 (PAPSActivity 모델 사용)
    
    Args:
        activity: PAPSActivity 인스턴스
        measurement_data: 측정 데이터
        student_grade: 학생 학년
    
    Returns:
        등급 계산 결과
    """
    if not activity.evaluation_criteria:
        return {'error': '등급 기준이 없는 종목입니다'}
    
    # 자동 계산 수행
    processed_data = process_measurement_data(
        activity.name, 
        measurement_data, 
        student_grade
    )
    
    # 평가 필드값 추출
    calculation_field = activity.evaluation_criteria.get('calculation_field')
    if not calculation_field:
        return {'error': '평가 기준 필드가 지정되지 않았습니다'}
    
    measurement_value = processed_data.get(calculation_field)
    if measurement_value is None:
        return {'error': f'측정값이 없습니다: {calculation_field}'}
    
    # 등급 계산
    grade_result = calculate_grade(
        measurement_value=measurement_value,
        evaluation_criteria=activity.evaluation_criteria,
        student_grade=student_grade
    )
    
    # 처리된 데이터도 함께 반환
    grade_result['processed_data'] = processed_data
    
    return grade_result


# ==================== PAPSRecord 자동 생성 유틸리티 ====================

def create_default_paps_records(session_activity, teacher_id):
    """
    특정 PAPSSessionActivity에 대한 모든 학생의 기본 PAPSRecord 생성
    
    Args:
        session_activity: PAPSSessionActivity 인스턴스
        teacher_id: 교사 ID
    
    Returns:
        dict: {'created_count': int, 'skipped_count': int, 'students': list}
    """
    from django.db import transaction
    from .models import PAPSRecord
    from accounts.models import Student, ClassTeacher
    
    created_count = 0
    skipped_count = 0
    students_info = []
    
    try:
        with transaction.atomic():
            # 해당 학년의 교사가 담당하는 모든 학급의 학생들 조회
            students = Student.objects.filter(
                school_class__grade=session_activity.grade,
                school_class__classteacher__teacher_id=teacher_id
            ).select_related('school_class', 'user')
            
            for student in students:
                # 이미 해당 활동에 대한 기록이 있는지 확인
                existing_record = PAPSRecord.objects.filter(
                    session_id=session_activity.session_id,
                    student_id=student.id,
                    activity_id=session_activity.activity_id
                ).first()
                
                if existing_record:
                    skipped_count += 1
                    students_info.append({
                        'student_id': student.id,
                        'student_name': student.user.get_full_name(),
                        'status': 'skipped',
                        'reason': 'already_exists'
                    })
                else:
                    # 새로운 PAPSRecord 생성 (빈 측정 데이터로)
                    PAPSRecord.objects.create(
                        session_id=session_activity.session_id,
                        student_id=student.id,
                        activity_id=session_activity.activity_id,
                        measured_by_teacher_id=teacher_id,
                        class_id=student.school_class.id,
                        student_grade=student.school_class.grade,
                        measurement_data={}  # 빈 측정 데이터
                    )
                    created_count += 1
                    students_info.append({
                        'student_id': student.id,
                        'student_name': student.user.get_full_name(),
                        'status': 'created',
                        'class_name': str(student.school_class)
                    })
            
    except Exception as e:
        return {
            'success': False,
            'error': f'PAPSRecord 생성 중 오류: {str(e)}',
            'created_count': 0,
            'skipped_count': 0
        }
    
    return {
        'success': True,
        'created_count': created_count,
        'skipped_count': skipped_count,
        'students': students_info
    }


def get_students_for_session_activity(session_activity, teacher_id):
    """
    세션 활동에 해당하는 학생들 조회 (권한 검증 포함)
    
    Args:
        session_activity: PAPSSessionActivity 인스턴스
        teacher_id: 교사 ID
    
    Returns:
        QuerySet: 해당 학년의 교사 담당 학생들
    """
    from accounts.models import Student, ClassTeacher
    
    return Student.objects.filter(
        school_class__grade=session_activity.grade,
        school_class__classteacher__teacher_id=teacher_id
    ).select_related('school_class', 'user')


def get_active_session_activities(session_id, grade=None):
    """
    활성 상태인 세션 활동들만 조회
    
    Args:
        session_id: PAPSSession ID
        grade: 학년 (optional)
    
    Returns:
        QuerySet: 활성 PAPSSessionActivity들
    """
    from .models import PAPSSessionActivity
    
    queryset = PAPSSessionActivity.objects.filter(
        session_id=session_id,
        is_active=True
    )
    
    if grade:
        queryset = queryset.filter(grade=grade)
    
    return queryset


def deactivate_session_activity(session_activity):
    """
    세션 활동을 비활성화
    기존 측정 데이터는 보존하되, 더 이상 활성 목록에 표시되지 않도록 함
    
    Args:
        session_activity: PAPSSessionActivity 인스턴스
    
    Returns:
        dict: 처리 결과
    """
    try:
        session_activity.is_active = False
        session_activity.save()
        
        return {
            'success': True,
            'message': f'{session_activity.get_grade_display()} 종목이 비활성화되었습니다.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'비활성화 중 오류: {str(e)}'
        }


def get_paps_records_for_active_activities(session_id, grade=None, student_id=None):
    """
    활성 세션 활동에 해당하는 PAPSRecord들만 조회
    
    Args:
        session_id: PAPSSession ID  
        grade: 학년 (optional)
        student_id: 학생 ID (optional)
    
    Returns:
        QuerySet: 활성 종목에 해당하는 PAPSRecord들
    """
    from .models import PAPSRecord
    
    # Manager 메서드 사용
    queryset = PAPSRecord.objects.active_for_session(session_id, grade)
    
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    
    return queryset


# ==================== 임시 성별 처리 ====================

def get_temporary_gender_info() -> Dict[str, str]:
    """
    임시 성별 정보 반환
    실제 성별 데이터가 없으므로 남녀 등급을 모두 보여주기 위한 임시 처리
    """
    return {
        'gender_status': 'both',
        'message': '성별 정보가 없어 남녀 등급을 모두 표시합니다'
    }