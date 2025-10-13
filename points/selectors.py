import uuid
from typing import Optional

from django.db.models import QuerySet

from common.utils import get_object
from points.models import PointPolicy, PointTransaction, StudentPointBalance
from points.filters import (
    PointPolicyFilter,
    PointTransactionFilter,
    StudentPointBalanceFilter,
)


# =============================================================================
# PointPolicy Selectors
# =============================================================================


def point_policy_list(*, filters=None) -> QuerySet[PointPolicy]:
    """포인트 정책 목록 조회"""
    filters = filters or {}

    qs = PointPolicy.objects.select_related("created_by").all()

    return PointPolicyFilter(filters, qs).qs


def point_policy_get(*, policy_id: uuid.UUID) -> Optional[PointPolicy]:
    """특정 포인트 정책 조회"""
    return get_object(PointPolicy.objects.select_related("created_by"), id=policy_id)


# =============================================================================
# PointTransaction Selectors
# =============================================================================


def point_transaction_list(*, filters=None) -> QuerySet[PointTransaction]:
    """포인트 거래 내역 목록 조회"""
    filters = filters or {}

    qs = PointTransaction.objects.select_related(
        "student",
        "student__user",
        "student__school_class",
        "policy",
        "processed_by",
        "processed_by__user",
    ).all()

    return PointTransactionFilter(filters, qs).qs


def point_transaction_get(*, transaction_id: uuid.UUID) -> Optional[PointTransaction]:
    """특정 포인트 거래 내역 조회"""
    return get_object(
        PointTransaction.objects.select_related(
            "student",
            "student__user",
            "student__school_class",
            "policy",
            "processed_by",
            "processed_by__user",
        ),
        id=transaction_id,
    )


# =============================================================================
# StudentPointBalance Selectors
# =============================================================================


def student_point_balance_list(*, filters=None) -> QuerySet[StudentPointBalance]:
    """학생 포인트 잔액 목록 조회"""
    filters = filters or {}

    qs = StudentPointBalance.objects.select_related(
        "student", "student__user", "student__school_class"
    ).all()

    return StudentPointBalanceFilter(filters, qs).qs


def student_point_balance_get(*, student_id: int) -> Optional[StudentPointBalance]:
    """특정 학생의 포인트 잔액 조회"""
    return get_object(
        StudentPointBalance.objects.select_related(
            "student", "student__user", "student__school_class"
        ),
        student_id=student_id,
    )


def student_point_balance_get_or_none(
    *, student_id: int
) -> Optional[StudentPointBalance]:
    """특정 학생의 포인트 잔액 조회 (없으면 None 반환)"""
    return get_object(
        StudentPointBalance.objects.select_related(
            "student", "student__user", "student__school_class"
        ),
        student_id=student_id,
    )
