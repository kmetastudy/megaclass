import django_filters

from accounts.models import Student


class StudentFilter(django_filters.FilterSet):
    """학생 필터"""

    # school_class__teachers 로 필터링 (ManyToMany 관계)
    teacher = django_filters.NumberFilter(
        field_name="school_class__teachers", lookup_expr="exact"
    )

    class Meta:
        model = Student
        fields = []
