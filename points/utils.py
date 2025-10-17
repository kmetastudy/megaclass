from points.models import PointTransaction


def format_transaction_for_student_display(transaction: PointTransaction) -> dict:
    """
    PointTransaction 객체를 학생 대시보드 템플릿용 dict로 변환

    Args:
        transaction: PointTransaction 인스턴스

    Returns:
        {
            'point_value': int,
            'policy_name': str | None,
            'teacher_name': str,
            'balance_after': int,
            'created_at': datetime,
            'is_earned': bool,
        }
    """
    return {
        "point_value": transaction.point_value,
        "policy_name": transaction.policy.name if transaction.policy else None,
        "teacher_name": transaction.processed_by.user.get_full_name(),
        "balance_after": transaction.balance_after,
        "created_at": transaction.created_at,
        "is_earned": transaction.point_value > 0,
    }
