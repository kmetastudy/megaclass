import django_filters

from points.models import PointPolicy, PointTransaction, StudentPointBalance


class PointPolicyFilter(django_filters.FilterSet):
    """포인트 정책 필터"""

    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = PointPolicy
        fields = ("created_by", "is_active", "name")


class PointTransactionFilter(django_filters.FilterSet):
    """포인트 거래 내역 필터"""

    created_at_gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at_lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = PointTransaction
        fields = ("student", "transaction_type", "policy", "processed_by")


class StudentPointBalanceFilter(django_filters.FilterSet):
    """학생 포인트 잔액 필터"""

    current_balance_gte = django_filters.NumberFilter(
        field_name="current_balance", lookup_expr="gte"
    )
    current_balance_lte = django_filters.NumberFilter(
        field_name="current_balance", lookup_expr="lte"
    )

    class Meta:
        model = StudentPointBalance
        fields = ("student",)
