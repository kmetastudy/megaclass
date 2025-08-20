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


# ==================== 상수 정의 ====================

# BMI에서 체지방률평가로 복사할 필드 매핑
BMI_TO_BODY_FAT_FIELD_MAP = {
    'bmi_height': 'body_fat_rate_test_height',
    'bmi_weight': 'body_fat_rate_test_weight'
}


# ==================== 유틸리티 함수 ====================

def get_korean_name(user):
    """Django User 객체의 한국식 이름 반환
    
    Args:
        user: Django User 객체
        
    Returns:
        str: "성이름" 형식의 한국식 이름 (예: 김철수)
    """
    if user.last_name and user.first_name:
        return f"{user.last_name}{user.first_name}"
    return user.get_full_name() or user.username


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


# ==================== 종목별 측정값 추출 ====================

def get_measurement_value(activity_name: str, measurement_data: Dict[str, Any]) -> Optional[float]:
    """종목별로 다른 JSON 키에서 실제 측정값 추출"""
    if not measurement_data:
        return None
        
    # 종목별 주요 측정값 키 매핑
    value_mapping = {
        'SHUTTLE_RUN': 'shuttle_run',
        'LONG_RUN_WALK': 'long_run_walk', 
        'STEP_TEST': 'step_test_pei',  # PEI 값 사용
        'SIT_REACH': 'sit_reach_best_record',
        'COMPREHENSIVE_FLEXIBILITY': 'flexibility_total_score',
        'PUSH_UP': 'push_up',
        'SIT_UP': 'sit_up', 
        'GRIP_STRENGTH': 'grip_strength_best',
        'FIFTY_METER_RUN': 'fifty_meter_run',
        'STANDING_LONG_JUMP': 'standing_long_jump_best_record',
        'BMI': 'bmi_bmi',
        'CARDIO_PRECISION_TEST': 'cardio_precision_pei',
        'BODY_FAT_RATE_TEST': 'body_fat_rate',  # 체지방률
        'POSTURE_TEST': 'posture_total_score',  # 자세평가 총점
        'SELF_BODY_TEST': 'self_body_total_score',  # 자기신체평가 총점
    }
    
    key = value_mapping.get(activity_name)
    if not key:
        return None
        
    value = measurement_data.get(key)
    if value is None:
        return None
        
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def get_activity_display_name(activity_name: str) -> str:
    """종목 코드를 한글 이름으로 변환"""
    name_mapping = {
        'SHUTTLE_RUN': '왕복오래달리기',
        'LONG_RUN_WALK': '오래달리기 걷기',
        'STEP_TEST': '스텝검사',
        'SIT_REACH': '앉아윗몸앞으로굽히기',
        'COMPREHENSIVE_FLEXIBILITY': '종합유연성',
        'PUSH_UP': '팔굽혀펴기',
        'SIT_UP': '윗몸 말아올리기',
        'GRIP_STRENGTH': '악력',
        'FIFTY_METER_RUN': '50m 달리기',
        'STANDING_LONG_JUMP': '제자리멀리뛰기',
        'BMI': '체질량 지수(BMI) 측정',
        'CARDIO_PRECISION_TEST': '심폐지구력정밀평가',
        'BODY_FAT_RATE_TEST': '체지방률평가',
        'POSTURE_TEST': '자세평가',
        'SELF_BODY_TEST': '자기신체평가',
    }
    return name_mapping.get(activity_name, activity_name)


def get_activity_unit(activity_name: str) -> str:
    """종목별 단위 반환"""
    unit_mapping = {
        'SHUTTLE_RUN': '회',
        'LONG_RUN_WALK': '분.초',
        'STEP_TEST': 'PEI',
        'SIT_REACH': 'cm',
        'COMPREHENSIVE_FLEXIBILITY': '점',
        'PUSH_UP': '회',
        'SIT_UP': '회',
        'GRIP_STRENGTH': 'kg',
        'FIFTY_METER_RUN': '초',
        'STANDING_LONG_JUMP': 'cm',
        'BMI': 'kg/m²',
        'CARDIO_PRECISION_TEST': 'PEI',
        'BODY_FAT_RATE_TEST': '%',
        'POSTURE_TEST': '점',
        'SELF_BODY_TEST': '점',
    }
    return unit_mapping.get(activity_name, '')


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

def get_boundary_grade(
    measurement_value: Union[float, Decimal],
    grade_criteria: Dict[str, Dict[str, Any]],
    calculation_method: str,
    grade_labels: Dict[str, str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    범위를 벗어난 측정값에 대해 경계 등급 계산
    
    Args:
        measurement_value: 측정값
        grade_criteria: 학년별 등급 기준 (예: {"grade_1": {"min": 96, "max": 103}, ...})
        calculation_method: 'higher_better' 또는 'lower_better'
        grade_labels: 등급 라벨 정보
    
    Returns:
        (grade_code, grade_label) 튜플 또는 (None, None)
    """
    if not grade_criteria:
        return None, None
    
    measurement_value = safe_decimal(measurement_value)
    
    # 모든 등급의 범위에서 전체 최소/최대값 찾기
    all_mins = []
    all_maxs = []
    
    for grade_key, range_info in grade_criteria.items():
        min_val = range_info.get('min')
        max_val = range_info.get('max')
        
        if min_val is not None:
            all_mins.append(min_val)
        if max_val is not None:
            all_maxs.append(max_val)
    
    if not all_mins and not all_maxs:
        return None, None
    
    # 전체 범위의 최소/최대값
    overall_min = min(all_mins) if all_mins else None
    overall_max = max(all_maxs) if all_maxs else None
    
    # 경계값 처리
    if calculation_method == 'lower_better':
        # 값이 낮을수록 좋음 (시간 등)
        if overall_min is not None and measurement_value < overall_min:
            # 최소값보다 작으면 1등급 (가장 좋음)
            return 'grade_1', grade_labels.get('grade_1', '1등급')
        elif overall_max is not None and measurement_value > overall_max:
            # 최대값보다 크면 5등급 (가장 나쁨)
            return 'grade_5', grade_labels.get('grade_5', '5등급')
    else:
        # 값이 높을수록 좋음 (기본)
        if overall_min is not None and measurement_value < overall_min:
            # 최소값보다 작으면 5등급 (가장 나쁨)
            return 'grade_5', grade_labels.get('grade_5', '5등급')
        elif overall_max is not None and measurement_value > overall_max:
            # 최대값보다 크면 1등급 (가장 좋음)
            return 'grade_1', grade_labels.get('grade_1', '1등급')
    
    return None, None


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
        
        # 등급이 결정되지 않은 경우 경계값 처리
        if grade_code is None:
            boundary_grade_code, boundary_grade_label = get_boundary_grade(
                measurement_value=measurement_value,
                grade_criteria=grade_criteria,
                calculation_method=calculation_method,
                grade_labels=grade_labels
            )
            if boundary_grade_code is not None:
                grade_code = boundary_grade_code
                grade_label = boundary_grade_label
        
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
        height = measurement_data.get('bmi_height')
        weight = measurement_data.get('bmi_weight')
        if height and weight:
            processed_data['bmi_bmi'] = float(calculate_bmi(height, weight))
        elif 'bmi_bmi' in processed_data:
            # 필수 입력값이 없는데 기존 계산값이 있으면 제거
            del processed_data['bmi_bmi']
    
    elif activity_name == 'STEP_TEST':
        # PEI 계산
        hr1 = measurement_data.get('step_test_heart_rate_1')
        hr2 = measurement_data.get('step_test_heart_rate_2')
        hr3 = measurement_data.get('step_test_heart_rate_3')
        if all([hr1, hr2, hr3]):
            # TODO: 성별 정보가 없어 임시로 학년만으로 고등학교 남학생 판단
            # 향후 성별 정보 추가 시 수정 필요 (고등학교 남학생만 다른 PEI 계산 공식 사용)
            is_male_hs = student_grade >= 10  # 임시로 고등학교 남학생 판단
            processed_data['step_test_pei'] = float(calculate_pei(hr1, hr2, hr3, is_male_high_school=is_male_hs))
        elif 'step_test_pei' in processed_data:
            # 필수 입력값이 하나라도 없는데 기존 계산값이 있으면 제거
            del processed_data['step_test_pei']
    
    elif activity_name == 'GRIP_STRENGTH':
        # 악력 최댓값 계산
        values = [
            measurement_data.get('grip_strength_right_hand_1'),
            measurement_data.get('grip_strength_left_hand_1'),
            measurement_data.get('grip_strength_right_hand_2'),
            measurement_data.get('grip_strength_left_hand_2')
        ]
        if any(v is not None for v in values):
            processed_data['grip_strength_best'] = float(calculate_max_value(*values))
        elif 'grip_strength_best' in processed_data:
            # 모든 입력값이 없는데 기존 계산값이 있으면 제거
            del processed_data['grip_strength_best']
    
    elif activity_name == 'SIT_REACH':
        # 앉아윗몸앞으로굽히기 최댓값
        first = measurement_data.get('sit_reach_first_attempt')
        second = measurement_data.get('sit_reach_second_attempt')
        if first is not None and second is not None:
            processed_data['sit_reach_best_record'] = float(calculate_max_value(first, second))
        elif 'sit_reach_best_record' in processed_data:
            # 필수 입력값이 하나라도 없는데 기존 계산값이 있으면 제거
            del processed_data['sit_reach_best_record']
    
    elif activity_name == 'STANDING_LONG_JUMP':
        # 제자리멀리뛰기 최댓값
        first = measurement_data.get('standing_long_jump_first_attempt')
        second = measurement_data.get('standing_long_jump_second_attempt')
        if first is not None and second is not None:
            processed_data['standing_long_jump_best_record'] = float(calculate_max_value(first, second))
        elif 'standing_long_jump_best_record' in processed_data:
            # 필수 입력값이 하나라도 없는데 기존 계산값이 있으면 제거
            del processed_data['standing_long_jump_best_record']
    
    elif activity_name == 'COMPREHENSIVE_FLEXIBILITY':
        # 종합유연성 총점
        boolean_fields = [
            'flexibility_shoulder_left', 'flexibility_shoulder_right', 'flexibility_body_left', 'flexibility_body_right',
            'flexibility_side_left', 'flexibility_side_right', 'flexibility_lower_body_left', 'flexibility_lower_body_right'
        ]
        # 실제로 입력된 필드가 있는지 확인
        has_any_input = any(field in measurement_data for field in boolean_fields)
        if has_any_input:
            values = [measurement_data.get(field, False) for field in boolean_fields]
            processed_data['flexibility_total_score'] = calculate_total_score(*values)
        elif 'flexibility_total_score' in processed_data:
            # 입력이 없는데 기존 계산값이 있으면 제거
            del processed_data['flexibility_total_score']
    
    
    elif activity_name == 'CARDIO_PRECISION_TEST':
        # 심폐지구력정밀평가 운동강도 계산
        avg_hr = measurement_data.get('cardio_precision_avg_heart_rate')
        if avg_hr:
            age = get_age_from_grade(student_grade)
            processed_data['cardio_precision_avg_intensity'] = calculate_exercise_intensity(avg_hr, age)
        elif 'cardio_precision_avg_intensity' in processed_data:
            # 필수 입력값이 없는데 기존 계산값이 있으면 제거
            del processed_data['cardio_precision_avg_intensity']
    
    elif activity_name == 'BODY_FAT_RATE_TEST':
        # 체지방률평가 BMI 계산
        height = measurement_data.get('body_fat_rate_test_height')
        weight = measurement_data.get('body_fat_rate_test_weight')
        if height and weight:
            processed_data['body_fat_rate_test_bmi'] = float(calculate_bmi(height, weight))
        elif 'body_fat_rate_test_bmi' in processed_data:
            # 필수 입력값이 없는데 기존 계산값이 있으면 제거
            del processed_data['body_fat_rate_test_bmi']
        
        # 근육량(%) 및 지방량(%) 계산
        body_fat_rate = measurement_data.get('body_fat_rate')
        if height and weight and body_fat_rate:
            weight_decimal = safe_decimal(weight)
            body_fat_rate_decimal = safe_decimal(body_fat_rate)
            
            # 근육량(%) = 0.85 × 체중 - (체중 × 체지방률) / 100 (소수점 첫째 자리에서 올림)
            muscle_mass = Decimal('0.85') * weight_decimal - (weight_decimal * body_fat_rate_decimal) / Decimal('100')
            muscle_mass_rounded = (muscle_mass * Decimal('10')).quantize(Decimal('1'), rounding=ROUND_UP) / Decimal('10')
            processed_data['body_fat_rate_muscle_mass'] = float(muscle_mass_rounded)
            
            # 지방량(%) = 체중 × 체지방률(%) (소수점 첫째 자리에서 올림)
            fat_mass = weight_decimal * body_fat_rate_decimal / Decimal('100')
            fat_mass_rounded = (fat_mass * Decimal('10')).quantize(Decimal('1'), rounding=ROUND_UP) / Decimal('10')
            processed_data['body_fat_rate_fat_mass'] = float(fat_mass_rounded)
        else:
            # 필수 입력값이 없는데 기존 계산값이 있으면 제거
            if 'body_fat_rate_muscle_mass' in processed_data:
                del processed_data['body_fat_rate_muscle_mass']
            if 'body_fat_rate_fat_mass' in processed_data:
                del processed_data['body_fat_rate_fat_mass']
    
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
                        'student_name': get_korean_name(student.user),
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
                        'student_name': get_korean_name(student.user),
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