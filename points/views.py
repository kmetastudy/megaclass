from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from points import selectors, services

# Create your views here.


@login_required
def teacher_dashboard(request):
    """선생님 포인트 관리 대시보드"""
    teacher = request.user.teacher

    # 1. StudentPointBalance 초기화 (없는 학생 생성)
    services.teacher_students_point_balance_ensure(teacher=teacher)

    # 2. 이번 주 시작일 계산 (월요일 00:00, Asia/Seoul)
    now = timezone.now()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # 3. 통계 데이터 조회
    basic_stats = selectors.teacher_dashboard_basic_stats_get(teacher=teacher)
    week_stats = selectors.teacher_week_points_stats_get(
        teacher=teacher, week_start=week_start
    )
    recent_activities = selectors.teacher_recent_activities_get(
        teacher=teacher, limit=5
    )
    top_students = selectors.teacher_top_students_get(teacher=teacher, limit=5)

    # 4. Context 구성
    context = {
        # 통계 카드
        "total_students": basic_stats["total_students"],
        "average_points": basic_stats["average_points"],
        "week_earned": week_stats["week_earned"],
        "week_deducted": week_stats["week_deducted"],
        # 리스트
        "recent_activities": recent_activities,
        "top_students": top_students,
        # 추가 정보
        "week_start_date": week_start,
    }
    print("[teacher_dashboard] context:", context)

    return render(request, "points/teacher/dashboard.html", context)
