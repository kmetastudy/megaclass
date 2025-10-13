import uuid

from django.db import models
from django.core.validators import MinValueValidator

from common.models import BaseModel
from accounts.models import Student, Teacher


class PointPolicy(BaseModel):
    """포인트 정책 설정 모델

    선생님이 자유롭게 활동별 포인트 정책을 생성합니다.
    정책의 default_point_value는 실제 부여 시 기본값으로 사용되며,
    상황에 따라 조정 가능합니다.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        verbose_name="생성한 교사",
        related_name="created_policies",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="활동명",
        help_text="예: 출석 체크, 숙제 제출, 프로젝트 발표",
    )
    default_point_value = models.IntegerField(
        verbose_name="기본 포인트 값",
        help_text="포인트 부여 시 기본값으로 사용됩니다. 양수는 적립, 음수는 차감",
    )
    description = models.TextField(
        blank=True, verbose_name="설명", help_text="포인트 정책에 대한 상세 설명"
    )
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "포인트 정책"
        verbose_name_plural = "포인트 정책"
        indexes = [
            models.Index(fields=["created_by", "is_active"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.default_point_value:+d}P)"


class PointTransaction(BaseModel):
    """포인트 거래 내역 모델

    모든 포인트 적립/차감 기록을 중앙에서 관리합니다.
    """

    class TransactionType(models.TextChoices):
        EARNED = "earned", "적립"
        DEDUCTED = "deducted", "차감"
        ADJUSTED = "adjusted", "조정"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        verbose_name="학생",
        related_name="point_transactions",
    )
    point_value = models.IntegerField(
        verbose_name="포인트 값", help_text="양수는 적립, 음수는 차감"
    )
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices, verbose_name="거래 유형"
    )
    policy = models.ForeignKey(
        PointPolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="관련 정책",
        related_name="transactions",
        help_text="수동 부여의 경우 null일 수 있음",
    )
    reason = models.TextField(verbose_name="사유", help_text="포인트 부여/차감 사유")
    processed_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        verbose_name="처리한 교사",
        related_name="processed_transactions",
    )
    balance_after = models.IntegerField(
        verbose_name="거래 후 잔액", help_text="거래 완료 후 학생의 포인트 잔액 스냅샷"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "포인트 거래 내역"
        verbose_name_plural = "포인트 거래 내역"
        indexes = [
            models.Index(fields=["student", "-created_at"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["processed_by"]),
        ]

    def __str__(self):
        sign = "+" if self.point_value >= 0 else ""
        return f"{self.student.user.get_full_name()} {sign}{self.point_value}P - {self.get_transaction_type_display()}"


class StudentPointBalance(BaseModel):
    """학생별 포인트 잔액 모델

    빠른 조회를 위한 캐시 테이블입니다.
    PointTransaction 생성 시 자동으로 업데이트됩니다.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        verbose_name="학생",
        related_name="point_balance",
    )
    current_balance = models.IntegerField(
        default=0,
        verbose_name="현재 잔액",
        validators=[MinValueValidator(0)],
        help_text="음수가 될 수 없습니다",
    )
    total_earned = models.IntegerField(
        default=0, verbose_name="총 적립", validators=[MinValueValidator(0)]
    )
    total_deducted = models.IntegerField(
        default=0, verbose_name="총 차감", validators=[MinValueValidator(0)]
    )
    last_transaction_at = models.DateTimeField(
        null=True, blank=True, verbose_name="마지막 거래 시각"
    )

    class Meta:
        ordering = ["-current_balance"]
        verbose_name = "학생 포인트 잔액"
        verbose_name_plural = "학생 포인트 잔액"
        indexes = [
            models.Index(fields=["-current_balance"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.current_balance}P"
