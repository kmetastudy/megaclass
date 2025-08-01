# Physical Education App - Development Guide

이 문서는 physical_education 앱의 개발 가이드라인을 제공합니다. PAPS(Physical Activity Promotion System) 기능 개발 시 참고하세요.

## 관련 문서 참조

필요시 다음 문서들을 참조할 수 있습니다:

- `@docs/physical_education/overview.md` - PAPS 전체 개요 및 측정 과정
- `@docs/physical_education/paps/required_input_examples.md` - 필수평가 UI 예시
- `@docs/physical_education/paps/optional_input_examples.md` - 선택평가 UI 예시
- `@docs/physical_education/paps/evaluation_criteria.md` - 상세 평가 기준
- `@docs/plans/physical_education_frontend_plan.md` - 프론트엔드 개발 계획

> **효율성 지침**: 위의 문서들은 특정 기능을 개발하거나 상세한 정보가 필요할 때만 읽어주세요. 매번 읽을 필요는 없습니다.

## 개요

physical_education 앱은 체육에 특화된 Django 앱으로, 주요 기능은 **PAPS(Physical Activity Promotion System)**입니다.

### PAPS란?

PAPS는 초/중/고등학교에서 학생들의 건강 체력을 평가하고 신체 활동을 증진시키기 위한 **필수 제도**입니다.

## 앱 구조

### 모델 구조 (5개 주요 모델)

```
PAPSCategory (9개)
├── 필수평가 (5개): 심폐지구력, 유연성, 근력/근지구력, 순발력, 비만
└── 선택평가 (4개): 심폐지구력정밀평가, 체지방률평가, 자세평가, 자기신체평가

PAPSActivity (15개)
├── 필수평가 활동 (11개): 왕복오래달리기, 오래달리기걷기, 스텝검사, 앉아윗몸앞으로굽히기, 종합유연성, 팔굽혀펴기, 윗몸말아올리기, 악력, 50m달리기, 제자리멀리뛰기, BMI측정
└── 선택평가 활동 (4개): 심폐지구력정밀평가, 체지방률평가, 자세평가, 자기신체평가

PAPSSession
└── 측정회차 관리 (정시/수시, 학년도별)

PAPSSessionActivity
└── 측정회차별 학년별 선택된 종목

PAPSRecord
└── 학생별 측정 기록
```

### 데이터 관리

#### 스키마 파일 위치

- `physical_education/data/measurement_schemas.json` - 15개 활동의 측정 스키마
- `physical_education/data/evaluation_criteria.json` - 11개 필수평가의 등급 기준

#### Management Commands

```bash
# PAPS 초기 데이터 생성 (카테고리 + 활동)
python manage.py init_paps_data

# 측정 스키마 및 평가 기준 업데이트
python manage.py update_paps_schemas

# 미리보기 (실제 업데이트 없이)
python manage.py update_paps_schemas --dry-run
```

## PAPS 평가 체계

### 필수평가 구조

각 체력요인별로 **한 종목씩 선택**하여 총 5개 종목 측정:

1. **심폐지구력** (3종목 중 1개 선택)

   - 왕복오래달리기: 완주 횟수(회)
   - 오래달리기걷기: 시간(분.초) → 총 시간(초)로 자동 계산
   - 스텝검사: 심박수 3회 측정 → PEI 자동 계산

2. **유연성** (2종목 중 1개 선택)

   - 앉아윗몸앞으로굽히기: 1차, 2차 → 최고값 자동 계산
   - 종합유연성: 8개 부위 성공/실패 → 총점 자동 계산

3. **근력/근지구력** (3종목 중 1개 선택)

   - 팔굽혀펴기: 성공 횟수(회)
   - 윗몸말아올리기: 성공 횟수(회)
   - 악력: 좌우 각 2회 측정 → 최고값 자동 계산

4. **순발력** (2종목 중 1개 선택)

   - 50m달리기: 완주 시간(초)
   - 제자리멀리뛰기: 1차, 2차 → 최고값 자동 계산

5. **비만** (1종목 필수)
   - BMI측정: 신장, 체중 → BMI 자동 계산

### 선택평가 (evaluation_criteria 없음)

- 심폐지구력정밀평가: 13개 필드 (심박수, 운동강도, 소비열량, 구간시간 등)
- 체지방률평가: 6개 필드 (키, 몸무게, BMI, 체지방률, 근육량, 지방량)
- 자세평가: 10개 필드 (7개 자세 항목 + 종합평가 + 문진 2개)
- 자기신체평가: 20개 문항 (1-6점 척도)

## 핵심 기능

### 자동 계산 로직 (`utils.py`)

```python
# BMI 계산: 체중(kg) ÷ [신장(m) × 신장(m)]
calculate_bmi(height_cm, weight_kg)

# PEI 계산: 초등/중등/고등(여) vs 고등(남) 구분
calculate_pei(hr1, hr2, hr3, duration=300, is_male_high_school=False)

# 최댓값 계산: 악력, 앉아윗몸앞으로굽히기, 제자리멀리뛰기
calculate_max_value(*values)

# 종합유연성 총점: 성공한 동작 수 (0-8점)
calculate_total_score(*boolean_values)

# 운동강도 계산: 평균 심박수 ÷ (220 - 나이) × 100
calculate_exercise_intensity(avg_heart_rate, age)
```

### 등급 계산

- **성별 구분**: 남/여 각각 다른 기준
- **학년별 기준**: 초4~고3 각각 다른 기준
- **등급 체계**: 1등급(최우수) ~ 5등급(개선필요)
- **BMI 특별 처리**: 마름/정상/과체중/경도비만/고도비만

## URL 구조

```
/physical_education/
├── teachers/                                         # 체육 교사 대시보드
├── teachers/paps/sessions/                           # 측정회차 관리 (목록/생성/삭제 통합)
├── teachers/paps/session-activities/                 # 측정종목 선택 (PAPSSessionActivity)
├── teachers/paps/measurement/required/               # 학급별필수평가입력
├── teachers/paps/measurement/optional/               # 학급별선택평가입력
└── api/paps/                                        # PAPS API 엔드포인트
    ├── save-measurement/                             # 측정 데이터 저장
    ├── calculate-grade/                              # 등급 계산
    └── activities/<category>/                        # 카테고리별 활동 조회
```

> **URL 설계 원칙**:
>
> - **5개 핵심 페이지 구조**: 홈, 측정회차관리, 측정종목선택, 학급별필수평가입력, 학급별선택평가입력
> - **간소화**: 
>   - 측정회차 생성/삭제는 `/teachers/paps/sessions/` 페이지에 통합
>   - 측정종목선택 페이지에서 session을 dropdown으로 선택 (URL에 session_id 불필요)
> - **모델 대응**: `session-activities`는 PAPSSessionActivity 모델과 직접 대응
> - **일관성**: 모든 교사용 기능은 `teachers/`로 시작, API는 `api/`로 시작

## 개발 패턴

### View 패턴

- **Function-based Views** 사용
- `@login_required` + `@teacher_required` 데코레이터 적용
- 권한 확인: teacher_id로 소유권 검증
- API는 JsonResponse 반환
- **통합 뷰 패턴**:
  - `paps_session_list_view`: 목록/생성/삭제 기능 통합 (POST 요청으로 구분)
  - `paps_session_activities_view`: session_id를 GET/POST 파라미터로 처리

### Form 패턴

```python
# 측정회차 폼: 학년도 기간 검증, 정시 중복 방지
PAPSSessionForm(teacher_id=request.user.teacher.id)

# 종목 선택 폼: 동적 필드 생성, 필수평가 검증
PAPSActivitySelectionForm(session=session, selected_grades=[6, 7, 8])
```

### 데이터 처리 패턴

```python
# 측정 데이터 자동 계산
processed_data = process_measurement_data(activity_name, measurement_data, student_grade)

# 등급 계산
grade_result = calculate_paps_grade(activity, measurement_data, student_grade)
```

## 중요 제약사항

### 측정회차 규칙

- **정시**: 학년도당 1회만 가능
- **수시**: 정시 이후 여러 번 가능
- **측정일자**: 해당 학년도 기간(3월~다음해 2월)만 허용
- **완료된 세션**: 수정/삭제 불가

### 종목 선택 규칙

- **필수평가**: 각 체력요인별 1개씩 반드시 선택
- **학년별 설정**: 동일 측정회차에서 학년별로 다른 종목 선택 가능
- **일괄 설정**: 여러 학년 동시 설정 지원

### 측정값 범위 (measurement_schemas.json 참조)

```json
{
  "SHUTTLE_RUN": { "min": 0, "max": 150, "unit": "회" },
  "SIT_REACH": { "min": -40.0, "max": 50.0, "unit": "cm" },
  "STEP_TEST": { "heart_rate": { "min": 20, "max": 250, "unit": "회/분" } },
  "BMI": { "height": { "min": 100.0, "max": 300.0, "unit": "cm" } }
}
```

## API 사용법

### 측정 데이터 저장

```javascript
POST / physical_education / api / paps / save -
  measurement /
    {
      session_id: "uuid",
      student_id: 123,
      activity_id: "uuid",
      measurement_data: {
        shuttles_completed: 85,
        // 활동별 측정 필드
      },
    };
```

### 등급 계산

```javascript
POST /physical_education/api/paps/calculate-grade/
{
  "activity_id": "uuid",
  "measurement_data": {...},
  "student_grade": 6
}

Response:
{
  "success": true,
  "grade_result": {
    "male_grade": "2등급",
    "female_grade": "1등급",
    "processed_data": {...}
  }
}
```

## 개발 시 주의사항

### 1. 한국어 UI

- 모든 사용자 인터페이스는 한국어
- 에러 메시지도 한국어로 표시
- 학년 표기: "초4", "중1", "고3" 형식

### 2. 성별 처리

- 현재는 성별 정보 없이 남녀 등급 모두 표시
- `get_temporary_gender_info()` 함수로 임시 처리

### 3. 학년 정보

- PAPS 대상: 초4~고3 (grade 4~12)
- `get_grade_from_number()`: 숫자 → 한글 학년 변환
- `get_age_from_grade()`: 학년 → 나이 계산

### 4. 데이터 무결성

- UUID 기반 Primary Key 사용
- Foreign Key는 UUID 필드로 참조 (실제 관계 설정 없이)
- unique_together 제약조건으로 중복 방지

### 5. 확장성 고려

- measurement_schema: JSON 기반 동적 필드 정의
- evaluation_criteria: JSON 기반 유연한 등급 기준
- Management command로 스키마 업데이트 지원

이 가이드라인을 따라 PAPS 기능을 안전하고 일관성 있게 개발하세요.
