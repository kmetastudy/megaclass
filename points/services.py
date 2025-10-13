import uuid
from typing import Optional
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from common.services import model_update
from points.models import PointPolicy, PointTransaction, StudentPointBalance
from accounts.models import Student, Teacher


# =============================================================================
# PointPolicy Services
# =============================================================================


@transaction.atomic
def point_policy_create(
    *,
    created_by: Teacher,
    name: str,
    default_point_value: int,
    description: str = "",
    is_active: bool = True,
) -> PointPolicy:
    """포인트 정책 생성"""
    point_policy = PointPolicy(
        created_by=created_by,
        name=name,
        default_point_value=default_point_value,
        description=description,
        is_active=is_active,
    )

    point_policy.full_clean()
    point_policy.save()

    return point_policy


@transaction.atomic
def point_policy_update(*, point_policy: PointPolicy, data: dict) -> PointPolicy:
    """포인트 정책 수정"""
    fields = ["name", "default_point_value", "description", "is_active"]

    point_policy, has_updated = model_update(
        instance=point_policy, fields=fields, data=data
    )

    return point_policy


@transaction.atomic
def point_policy_delete(*, point_policy: PointPolicy) -> None:
    """포인트 정책 삭제 (비활성화)"""
    point_policy.is_active = False
    point_policy.save(update_fields=["is_active", "updated_at"])


# =============================================================================
# PointTransaction Services (핵심 비즈니스 로직)
# =============================================================================


@transaction.atomic
def point_transaction_create(
    *,
    student: Student,
    point_value: int,
    transaction_type: str,
    reason: str,
    processed_by: Teacher,
    policy: Optional[PointPolicy] = None,
) -> PointTransaction:
    """
    포인트 거래 생성 (적립/차감)

    Args:
        student: 대상 학생
        point_value: 포인트 값 (양수: 적립, 음수: 차감)
        transaction_type: 거래 유형 (earned, deducted, adjusted)
        reason: 사유
        processed_by: 처리한 교사
        policy: 관련 정책 (선택사항)

    Returns:
        생성된 PointTransaction 객체

    Raises:
        ValidationError: 잔액 부족 시
    """

    # 1. StudentPointBalance 조회 또는 생성
    balance, created = StudentPointBalance.objects.get_or_create(
        student=student,
        defaults={
            "current_balance": 0,
            "total_earned": 0,
            "total_deducted": 0,
        },
    )

    # 2. 새 잔액 계산
    new_balance = balance.current_balance + point_value

    # 3. 잔액 검증 (음수 방지)
    if new_balance < 0:
        raise ValidationError(
            f"잔액이 부족합니다. 현재 잔액: {balance.current_balance}, 차감 요청: {abs(point_value)}"
        )

    # 4. PointTransaction 생성
    point_transaction = PointTransaction(
        student=student,
        point_value=point_value,
        transaction_type=transaction_type,
        reason=reason,
        processed_by=processed_by,
        policy=policy,
        balance_after=new_balance,  # 거래 후 잔액 스냅샷
    )

    point_transaction.full_clean()
    point_transaction.save()

    # 5. StudentPointBalance 업데이트
    balance.current_balance = new_balance

    if point_value > 0:
        balance.total_earned += point_value
    else:
        balance.total_deducted += abs(point_value)

    balance.last_transaction_at = timezone.now()
    balance.full_clean()
    balance.save(
        update_fields=[
            "current_balance",
            "total_earned",
            "total_deducted",
            "last_transaction_at",
            "updated_at",
        ]
    )

    return point_transaction


@transaction.atomic
def point_transaction_bulk_create(
    *,
    students: list[Student],
    point_value: int,
    transaction_type: str,
    reason: str,
    processed_by: Teacher,
    policy: Optional[PointPolicy] = None,
) -> list[PointTransaction]:
    """
    여러 학생에게 일괄 포인트 부여/차감

    Args:
        students: 대상 학생 리스트
        point_value: 포인트 값 (양수: 적립, 음수: 차감)
        transaction_type: 거래 유형
        reason: 사유
        processed_by: 처리한 교사
        policy: 관련 정책 (선택사항)

    Returns:
        생성된 PointTransaction 객체 리스트
    """
    transactions = []

    for student in students:
        transaction = point_transaction_create(
            student=student,
            point_value=point_value,
            transaction_type=transaction_type,
            reason=reason,
            processed_by=processed_by,
            policy=policy,
        )
        transactions.append(transaction)

    return transactions


# =============================================================================
# StudentPointBalance Services
# =============================================================================


def student_point_balance_get_or_create(
    *, student: Student
) -> tuple[StudentPointBalance, bool]:
    """
    학생 포인트 잔액 조회 또는 생성

    Returns:
        (StudentPointBalance 객체, 생성 여부)
    """
    return StudentPointBalance.objects.get_or_create(
        student=student,
        defaults={
            "current_balance": 0,
            "total_earned": 0,
            "total_deducted": 0,
        },
    )
