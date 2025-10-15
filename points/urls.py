from django.urls import path, include

from points.apis import (
    # PointPolicy APIs
    PointPolicyListApi,
    PointPolicyDetailApi,
    PointPolicyCreateApi,
    PointPolicyUpdateApi,
    PointPolicyDeleteApi,
    # PointTransaction APIs
    PointTransactionCreateApi,
    PointTransactionListApi,
    # StudentPointBalance APIs
    StudentPointBalanceListApi,
    StudentPointBalanceDetailApi,
)
from points.views import teacher_dashboard

app_name = "points"

# PointPolicy URL patterns
policy_patterns = [
    path("", PointPolicyListApi.as_view(), name="policy-list"),
    path("create/", PointPolicyCreateApi.as_view(), name="policy-create"),
    path("<uuid:policy_id>/", PointPolicyDetailApi.as_view(), name="policy-detail"),
    path(
        "<uuid:policy_id>/update/",
        PointPolicyUpdateApi.as_view(),
        name="policy-update",
    ),
    path(
        "<uuid:policy_id>/delete/",
        PointPolicyDeleteApi.as_view(),
        name="policy-delete",
    ),
]

# PointTransaction URL patterns
transaction_patterns = [
    path("", PointTransactionListApi.as_view(), name="transaction-list"),
    path("create/", PointTransactionCreateApi.as_view(), name="transaction-create"),
]

# StudentPointBalance URL patterns
balance_patterns = [
    path("", StudentPointBalanceListApi.as_view(), name="balance-list"),
    path(
        "<int:student_id>/",
        StudentPointBalanceDetailApi.as_view(),
        name="balance-detail",
    ),
]

# API patterns (exported for api app)
api_patterns = [
    path("policies/", include((policy_patterns, "policies"))),
    path("transactions/", include((transaction_patterns, "transactions"))),
    path("balances/", include((balance_patterns, "balances"))),
]

# View patterns
urlpatterns = [
    # Teacher views
    path("teacher/", teacher_dashboard, name="teacher_dashboard"),
]
