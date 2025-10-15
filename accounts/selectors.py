from typing import Optional
from django.db.models import QuerySet

from accounts.models import Student
from accounts.filters import StudentFilter


def student_list(*, filters=None) -> QuerySet[Student]:
    """
    학생 목록 조회

    Args:
        filters: 필터 딕셔너리 (예: {'teacher': teacher_id})

    Returns:
        Student QuerySet
    """
    filters = filters or {}

    qs = Student.objects.select_related("user", "school_class").all()

    return StudentFilter(filters, qs).qs
