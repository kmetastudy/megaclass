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


# =============================================================================
# Teacher Dashboard Selectors
# =============================================================================


def teacher_dashboard_basic_stats_get(*, teacher) -> dict:
    """
    선생님 대시보드 기본 통계
    - 총 학생 수
    - 평균 포인트

    Args:
        teacher: Teacher 인스턴스

    Returns:
        {
            'total_students': int,
            'average_points': float,
        }
    """
    from accounts.selectors import student_list
    from django.db.models import Avg

    # teacher 필터로 담당 학생 조회
    students = student_list(filters={"teacher": teacher.id})
    total_students = students.count()

    # StudentPointBalance에서 평균 계산
    student_ids = students.values_list("id", flat=True)
    avg_points = (
        StudentPointBalance.objects.filter(student_id__in=student_ids).aggregate(
            avg=Avg("current_balance")
        )["avg"]
    )

    return {
        "total_students": total_students,
        "average_points": round(avg_points, 1) if avg_points else 0.0,
    }


def teacher_week_points_stats_get(*, teacher, week_start) -> dict:
    """
    이번 주 포인트 적립/차감 통계

    Args:
        teacher: Teacher 인스턴스
        week_start: 주 시작일 (월요일 00:00)

    Returns:
        {
            'week_earned': int,
            'week_deducted': int,
        }
    """
    from accounts.selectors import student_list
    from django.db.models import Sum

    students = student_list(filters={"teacher": teacher.id})
    student_ids = students.values_list("id", flat=True)

    # 이번 주 거래 내역
    transactions = PointTransaction.objects.filter(
        student_id__in=student_ids, created_at__gte=week_start
    )

    # 적립 (point_value > 0)
    earned = (
        transactions.filter(point_value__gt=0).aggregate(total=Sum("point_value"))[
            "total"
        ]
        or 0
    )

    # 차감 (point_value < 0)
    deducted = (
        transactions.filter(point_value__lt=0).aggregate(total=Sum("point_value"))[
            "total"
        ]
        or 0
    )

    return {
        "week_earned": earned,
        "week_deducted": abs(deducted),  # 양수로 변환
    }


def teacher_recent_activities_get(*, teacher, limit: int = 5) -> list[dict]:
    """
    최근 포인트 거래 내역

    Args:
        teacher: Teacher 인스턴스
        limit: 조회할 개수

    Returns:
        [
            {
                'student_name': str,
                'point_value': int,
                'policy_name': str | None,
                'created_at': datetime,
            }
        ]
    """
    from accounts.selectors import student_list

    students = student_list(filters={"teacher": teacher.id})
    student_ids = students.values_list("id", flat=True)

    transactions = (
        PointTransaction.objects.filter(student_id__in=student_ids)
        .select_related("student__user", "policy")
        .order_by("-created_at")[:limit]
    )

    return [
        {
            "student_name": t.student.user.get_full_name(),
            "point_value": t.point_value,
            "policy_name": t.policy.name if t.policy else None,
            "created_at": t.created_at,
        }
        for t in transactions
    ]


def teacher_top_students_get(*, teacher, limit: int = 5) -> list[dict]:
    """
    포인트 상위 학생 목록

    Args:
        teacher: Teacher 인스턴스
        limit: 조회할 개수

    Returns:
        [
            {
                'rank': int,
                'student_name': str,
                'student_id': str,
                'current_balance': int,
            }
        ]
    """
    from accounts.selectors import student_list

    students = student_list(filters={"teacher": teacher.id})
    student_ids = students.values_list("id", flat=True)

    top_balances = (
        StudentPointBalance.objects.filter(student_id__in=student_ids)
        .select_related("student__user")
        .order_by("-current_balance")[:limit]
    )

    return [
        {
            "rank": idx + 1,
            "student_name": balance.student.user.get_full_name(),
            "student_id": balance.student.student_id,
            "current_balance": balance.current_balance,
        }
        for idx, balance in enumerate(top_balances)
    ]
