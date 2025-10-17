import uuid
from typing import Optional

from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from points.models import PointPolicy, PointTransaction, StudentPointBalance
from points import selectors, services
from accounts.models import Student, Teacher
from common.utils import get_object


# =============================================================================
# PointPolicy APIs
# =============================================================================


class PointPolicyListApi(APIView):
    """포인트 정책 목록 조회"""

    permission_classes = [IsAuthenticated]

    class FilterSerializer(serializers.Serializer):
        created_by = serializers.IntegerField(required=False)
        is_active = serializers.BooleanField(required=False)
        name = serializers.CharField(required=False)

    class OutputSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        created_by_id = serializers.IntegerField(source="created_by.id")
        created_by_name = serializers.CharField(source="created_by.user.get_full_name")
        name = serializers.CharField()
        default_point_value = serializers.IntegerField()
        description = serializers.CharField()
        is_active = serializers.BooleanField()
        created_at = serializers.DateTimeField()

    def get(self, request):
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)

        policies = selectors.point_policy_list(
            filters=filters_serializer.validated_data
        )
        data = self.OutputSerializer(policies, many=True).data

        return Response(data)


class PointPolicyDetailApi(APIView):
    """포인트 정책 상세 조회"""

    permission_classes = [IsAuthenticated]

    class OutputSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        created_by_id = serializers.IntegerField(source="created_by.id")
        created_by_name = serializers.CharField(source="created_by.user.get_full_name")
        name = serializers.CharField()
        default_point_value = serializers.IntegerField()
        description = serializers.CharField()
        is_active = serializers.BooleanField()
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField()

    def get(self, request, policy_id):
        policy = selectors.point_policy_get(policy_id=policy_id)

        if not policy:
            return Response(
                {"error": "포인트 정책을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = self.OutputSerializer(policy).data
        return Response(data)


class PointPolicyCreateApi(APIView):
    """포인트 정책 생성"""

    permission_classes = [IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=100)
        default_point_value = serializers.IntegerField()
        description = serializers.CharField(required=False, allow_blank=True)
        is_active = serializers.BooleanField(default=True)

    class OutputSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        name = serializers.CharField()
        default_point_value = serializers.IntegerField()
        description = serializers.CharField()
        is_active = serializers.BooleanField()
        created_at = serializers.DateTimeField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 교사 권한 확인
        try:
            teacher = request.user.teacher
        except AttributeError:
            return Response(
                {"error": "교사 권한이 필요합니다."}, status=status.HTTP_403_FORBIDDEN
            )

        policy = services.point_policy_create(
            created_by=teacher, **serializer.validated_data
        )

        return Response(
            {
                "id": str(policy.id),
                "message": "포인트 정책이 생성되었습니다.",
                "data": self.OutputSerializer(policy).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PointPolicyUpdateApi(APIView):
    """포인트 정책 수정"""

    permission_classes = [IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=100, required=False)
        default_point_value = serializers.IntegerField(required=False)
        description = serializers.CharField(required=False, allow_blank=True)
        is_active = serializers.BooleanField(required=False)

    class OutputSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        name = serializers.CharField()
        default_point_value = serializers.IntegerField()
        description = serializers.CharField()
        is_active = serializers.BooleanField()
        updated_at = serializers.DateTimeField()

    def post(self, request, policy_id):
        policy = selectors.point_policy_get(policy_id=policy_id)

        if not policy:
            return Response(
                {"error": "포인트 정책을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 권한 확인: 생성한 교사만 수정 가능
        try:
            teacher = request.user.teacher
            if policy.created_by.id != teacher.id:
                return Response(
                    {"error": "해당 정책을 수정할 권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except AttributeError:
            return Response(
                {"error": "교사 권한이 필요합니다."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_policy = services.point_policy_update(
            point_policy=policy, data=serializer.validated_data
        )

        return Response(
            {
                "message": "포인트 정책이 수정되었습니다.",
                "data": self.OutputSerializer(updated_policy).data,
            }
        )


class PointPolicyDeleteApi(APIView):
    """포인트 정책 삭제 (비활성화)"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, policy_id):
        policy = selectors.point_policy_get(policy_id=policy_id)

        if not policy:
            return Response(
                {"error": "포인트 정책을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 권한 확인
        try:
            teacher = request.user.teacher
            if policy.created_by.id != teacher.id:
                return Response(
                    {"error": "해당 정책을 삭제할 권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except AttributeError:
            return Response(
                {"error": "교사 권한이 필요합니다."}, status=status.HTTP_403_FORBIDDEN
            )

        services.point_policy_delete(point_policy=policy)

        return Response({"message": "포인트 정책이 삭제되었습니다."})


# =============================================================================
# PointTransaction APIs (핵심 MVP 기능)
# =============================================================================


class PointTransactionCreateApi(APIView):
    """포인트 부여/차감 (MVP 핵심 기능)"""

    permission_classes = [IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        student_ids = serializers.ListField(
            child=serializers.IntegerField(), min_length=1
        )
        point_value = serializers.IntegerField()
        transaction_type = serializers.ChoiceField(
            choices=["earned", "deducted", "adjusted"]
        )
        reason = serializers.CharField()
        policy_id = serializers.UUIDField(required=False, allow_null=True)

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 교사 권한 확인
        try:
            teacher = request.user.teacher
        except AttributeError:
            return Response(
                {"error": "교사 권한이 필요합니다."}, status=status.HTTP_403_FORBIDDEN
            )

        # 학생 조회
        student_ids = serializer.validated_data["student_ids"]
        students = Student.objects.filter(id__in=student_ids)

        if len(students) != len(student_ids):
            return Response(
                {"error": "일부 학생을 찾을 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 정책 조회 (선택사항)
        policy = None
        policy_id = serializer.validated_data.get("policy_id")
        if policy_id:
            policy = selectors.point_policy_get(policy_id=policy_id)
            if not policy:
                return Response(
                    {"error": "포인트 정책을 찾을 수 없습니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # 일괄 포인트 부여/차감
        try:
            transactions = services.point_transaction_bulk_create(
                students=list(students),
                point_value=serializer.validated_data["point_value"],
                transaction_type=serializer.validated_data["transaction_type"],
                reason=serializer.validated_data["reason"],
                processed_by=teacher,
                policy=policy,
            )

            return Response(
                {
                    "message": f"{len(transactions)}명의 학생에게 포인트가 처리되었습니다.",
                    "processed_count": len(transactions),
                },
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PointTransactionListApi(APIView):
    """포인트 거래 내역 목록 조회"""

    permission_classes = [IsAuthenticated]

    class FilterSerializer(serializers.Serializer):
        student = serializers.IntegerField(required=False)
        transaction_type = serializers.CharField(required=False)
        policy = serializers.UUIDField(required=False)
        processed_by = serializers.IntegerField(required=False)
        created_at_gte = serializers.DateTimeField(required=False)
        created_at_lte = serializers.DateTimeField(required=False)

    class OutputSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        student_id = serializers.IntegerField(source="student.id")
        student_name = serializers.CharField(source="student.user.get_full_name")
        point_value = serializers.IntegerField()
        transaction_type = serializers.CharField()
        transaction_type_display = serializers.CharField(
            source="get_transaction_type_display"
        )
        reason = serializers.CharField()
        processed_by_id = serializers.IntegerField(source="processed_by.id")
        processed_by_name = serializers.CharField(
            source="processed_by.user.get_full_name"
        )
        balance_after = serializers.IntegerField()
        policy_id = serializers.UUIDField(source="policy.id", allow_null=True)
        policy_name = serializers.CharField(source="policy.name", allow_null=True)
        created_at = serializers.DateTimeField()

    def get(self, request):
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)

        transactions = selectors.point_transaction_list(
            filters=filters_serializer.validated_data
        )
        data = self.OutputSerializer(transactions, many=True).data

        return Response(data)


# =============================================================================
# StudentPointBalance APIs
# =============================================================================


class StudentPointBalanceListApi(APIView):
    """학생 포인트 잔액 목록 조회"""

    permission_classes = [IsAuthenticated]

    class FilterSerializer(serializers.Serializer):
        student = serializers.IntegerField(required=False)
        current_balance_gte = serializers.IntegerField(required=False)
        current_balance_lte = serializers.IntegerField(required=False)

    class OutputSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        student_id = serializers.IntegerField(source="student.id")
        student_name = serializers.CharField(source="student.user.get_full_name")
        class_name = serializers.CharField(source="student.school_class.__str__")
        grade = serializers.IntegerField(source="student.school_class.grade")
        class_number = serializers.IntegerField(source="student.school_class.class_number")
        current_balance = serializers.IntegerField()
        total_earned = serializers.IntegerField()
        total_deducted = serializers.IntegerField()
        last_transaction_at = serializers.DateTimeField()

    def get(self, request):
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)

        balances = selectors.student_point_balance_list(
            filters=filters_serializer.validated_data
        )
        data = self.OutputSerializer(balances, many=True).data

        return Response(data)


class StudentPointBalanceDetailApi(APIView):
    """학생 포인트 잔액 상세 조회"""

    permission_classes = [IsAuthenticated]

    class OutputSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        student_id = serializers.IntegerField(source="student.id")
        student_name = serializers.CharField(source="student.user.get_full_name")
        class_name = serializers.CharField(source="student.school_class.__str__")
        current_balance = serializers.IntegerField()
        total_earned = serializers.IntegerField()
        total_deducted = serializers.IntegerField()
        last_transaction_at = serializers.DateTimeField()
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField()

    def get(self, request, student_id):
        balance = selectors.student_point_balance_get(student_id=student_id)

        if not balance:
            return Response(
                {"error": "해당 학생의 포인트 잔액을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = self.OutputSerializer(balance).data
        return Response(data)
