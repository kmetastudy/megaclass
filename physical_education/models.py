import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class PAPSCategory(models.Model):
    """PAPS 체력요인 모델 (필수평가 5개 + 선택평가 4개)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 평가 구분
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"

    EVALUATION_TYPE_CHOICES = [
        (REQUIRED, "필수평가"),
        (OPTIONAL, "선택평가"),
    ]

    # 체력요인 코드
    CARDIO = "CARDIO"  # 심폐지구력
    FLEXIBILITY = "FLEXIBILITY"  # 유연성
    STRENGTH = "STRENGTH"  # 근력/근지구력
    AGILITY = "AGILITY"  # 순발력
    BODY_FAT = "BODY_FAT"  # 체지방
    CARDIO_PRECISION = "CARDIO_PRECISION"  # 심폐지구력정밀평가
    BODY_FAT_RATE = "BODY_FAT_RATE"  # 체지방률평가
    POSTURE = "POSTURE"  # 자세평가
    SELF_BODY = "SELF_BODY"  # 자기신체평가

    CATEGORY_CHOICES = [
        (CARDIO, "심폐지구력"),
        (FLEXIBILITY, "유연성"),
        (STRENGTH, "근력/근지구력"),
        (AGILITY, "순발력"),
        (BODY_FAT, "비만"),
        (CARDIO_PRECISION, "심폐지구력정밀평가"),
        (BODY_FAT_RATE, "체지방률평가"),
        (POSTURE, "자세평가"),
        (SELF_BODY, "자기신체평가"),
    ]

    name = models.CharField(max_length=30, choices=CATEGORY_CHOICES, unique=True)
    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPE_CHOICES)
    order = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(9)])

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.get_name_display()


class PAPSActivity(models.Model):
    """PAPS 측정 종목 모델 (필수평가 11개 + 선택평가 4개)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 종목 코드
    SHUTTLE_RUN = "SHUTTLE_RUN"  # 왕복오래달리기
    LONG_RUN_WALK = "LONG_RUN_WALK"  # 오래달리기 걷기
    STEP_TEST = "STEP_TEST"  # 스텝검사
    SIT_REACH = "SIT_REACH"  # 앉아윗몸앞으로굽히기
    COMPREHENSIVE_FLEXIBILITY = "COMPREHENSIVE_FLEXIBILITY"  # 종합유연성
    PUSH_UP = "PUSH_UP"  # 팔굽혀펴기
    SIT_UP = "SIT_UP"  # 윗몸 말아올리기
    GRIP_STRENGTH = "GRIP_STRENGTH"  # 악력
    FIFTY_METER_RUN = "FIFTY_METER_RUN"  # 50m 달리기
    STANDING_LONG_JUMP = "STANDING_LONG_JUMP"  # 제자리멀리뛰기
    BMI = "BMI"  # 체질량 지수
    CARDIO_PRECISION_TEST = "CARDIO_PRECISION_TEST"  # 심폐지구력정밀평가
    BODY_FAT_RATE_TEST = "BODY_FAT_RATE_TEST"  # 체지방률평가
    POSTURE_TEST = "POSTURE_TEST"  # 자세평가
    SELF_BODY_TEST = "SELF_BODY_TEST"  # 자기신체평가

    ACTIVITY_CHOICES = [
        (SHUTTLE_RUN, "왕복오래달리기"),
        (LONG_RUN_WALK, "오래달리기 걷기"),
        (STEP_TEST, "스텝검사"),
        (SIT_REACH, "앉아윗몸앞으로굽히기"),
        (COMPREHENSIVE_FLEXIBILITY, "종합유연성"),
        (PUSH_UP, "팔굽혀펴기"),
        (SIT_UP, "윗몸 말아올리기"),
        (GRIP_STRENGTH, "악력"),
        (FIFTY_METER_RUN, "50m 달리기"),
        (STANDING_LONG_JUMP, "제자리멀리뛰기"),
        (BMI, "체질량 지수(BMI) 측정"),
        (CARDIO_PRECISION_TEST, "심폐지구력정밀평가"),
        (BODY_FAT_RATE_TEST, "체지방률평가"),
        (POSTURE_TEST, "자세평가"),
        (SELF_BODY_TEST, "자기신체평가"),
    ]

    name = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, unique=True)
    category_id = models.UUIDField()  # PAPSCategory ID 참조
    measurement_schema = models.JSONField()  # 측정 데이터 구조 정의
    evaluation_criteria = models.JSONField(blank=True, null=True)  # 등급 계산 기준

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_name_display()


class PAPSSession(models.Model):
    """PAPS 측정 회차 모델"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 측정 구분
    REGULAR = "REGULAR"  # 정시
    SUPPLEMENTARY = "SUPPLEMENTARY"  # 수시

    SESSION_TYPE_CHOICES = [
        (REGULAR, "정시"),
        (SUPPLEMENTARY, "수시"),
    ]

    teacher_id = models.IntegerField()  # Teacher ID 참조
    school_year = models.IntegerField(
        validators=[MinValueValidator(2020), MaxValueValidator(2050)]
    )
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    measurement_date = models.DateField()

    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-school_year", "-measurement_date"]

    def __str__(self):
        return f"{self.school_year}년도 {self.get_session_type_display()} - {self.name}"


class PAPSSessionActivity(models.Model):
    """측정 회차별 학년별 선택된 종목"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 학년 선택지 (PAPS 대상: 초4-고3)
    GRADE_CHOICES = [
        (4, "초등학교 4학년"),
        (5, "초등학교 5학년"),
        (6, "초등학교 6학년"),
        (7, "중학교 1학년"),
        (8, "중학교 2학년"),
        (9, "중학교 3학년"),
        (10, "고등학교 1학년"),
        (11, "고등학교 2학년"),
        (12, "고등학교 3학년"),
    ]

    session_id = models.UUIDField()  # PAPSSession ID 참조
    grade = models.IntegerField(
        choices=GRADE_CHOICES, validators=[MinValueValidator(4), MaxValueValidator(12)]
    )
    category_id = models.UUIDField()  # PAPSCategory ID 참조
    activity_id = models.UUIDField()  # PAPSActivity ID 참조

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["session_id", "grade", "category_id"]

    def __str__(self):
        return f"{self.get_grade_display()} - 선택 종목"


class PAPSRecord(models.Model):
    """PAPS 학생별 측정 기록 모델"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # PAPS 등급
    GRADE_CHOICES = [
        ("1", "1등급"),
        ("2", "2등급"),
        ("3", "3등급"),
        ("4", "4등급"),
        ("5", "5등급"),
    ]

    session_id = models.UUIDField()  # PAPSSession ID 참조
    student_id = models.IntegerField()  # Student ID 참조
    activity_id = models.UUIDField()  # PAPSActivity ID 참조
    measured_by_teacher_id = models.IntegerField()  # Teacher ID 참조
    class_id = models.IntegerField()  # Class ID 참조

    student_grade = models.IntegerField(
        validators=[MinValueValidator(4), MaxValueValidator(12)]
    )
    measurement_data = models.JSONField()  # 측정 데이터
    evaluation_grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)

    measured_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-measured_at"]
        unique_together = ["session_id", "student_id", "activity_id"]

    def __str__(self):
        grade = self.evaluation_grade if self.evaluation_grade else "미산정"
        return f"PAPS 측정 기록 - {grade}등급"
