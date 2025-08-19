from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from teacher.decorators import teacher_required
from .models import (
    PAPSSession,
    PAPSSessionActivity,
    PAPSCategory,
    PAPSActivity,
    PAPSRecord,
)
from .forms import PAPSSessionForm, PAPSActivitySelectionForm
from .utils import calculate_paps_grade, get_measurement_value, get_activity_display_name, get_activity_unit, get_grade_from_number, get_korean_name
from accounts.models import ClassTeacher, Class, Student
import json


# ================= 헬퍼 함수들 =================


def get_grade_display_name(grade):
    """학년 숫자를 한글 표시로 변환"""
    if grade <= 6:
        return f"초등학교 {grade}학년"
    elif grade <= 9:
        return f"중학교 {grade - 6}학년"
    else:
        return f"고등학교 {grade - 9}학년"


def get_student_gender(student):
    """학생 성별 정보 추출 (임시로 이름 기반 추정)"""
    # 실제로는 User 모델에 성별 필드가 있거나 Profile 모델을 통해 관리해야 함
    # 현재는 임시로 이름 기반으로 추정
    name = get_korean_name(student.user)

    # 한국 이름의 일반적인 패턴으로 간단히 추정 (실제로는 정확한 데이터가 필요)
    male_endings = ["수", "호", "민", "진", "현", "우", "석", "준", "혁", "영"]
    female_endings = ["희", "은", "영", "민", "지", "나", "아", "라", "인", "연"]

    if name:
        last_char = name[-1]
        if last_char in male_endings:
            return "M"
        elif last_char in female_endings:
            return "F"

    # 기본값은 남성으로 설정 (실제로는 필수 필드여야 함)
    return "M"


def get_student_number_from_id(student_id):
    """학번에서 번호 추출 (예: 'S001' -> 1)"""
    try:
        # 학번 형식에 따라 조정 필요
        if student_id.startswith("S"):
            return int(student_id[1:])
        return int(student_id)
    except (ValueError, TypeError):
        return 1


@login_required
@teacher_required
def teacher_dashboard(request):
    """체육 교사 대시보드 뷰"""
    teacher_id = request.user.teacher.id
    from datetime import datetime, timedelta
    from django.db.models import Count, Q
    from collections import defaultdict

    # 기본 통계 데이터 계산
    total_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).count()

    # 진행 중인 측정회차 (완료되지 않은 회차)
    active_sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id, is_completed=False
    ).count()

    # 이번 달 측정회차
    current_month = datetime.now().month
    current_year = datetime.now().year

    this_month_sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id,
        measurement_date__month=current_month,
        measurement_date__year=current_year,
    ).count()

    # 총 측정 기록 수 (참여 학생 수로 사용)
    total_records = PAPSRecord.objects.filter(measured_by_teacher_id=teacher_id).count()

    # 담당 학급 정보 조회
    teacher_classes = ClassTeacher.objects.filter(
        teacher=request.user.teacher
    ).select_related('class_instance')
    
    class_info = []
    for ct in teacher_classes:
        student_count = Student.objects.filter(school_class=ct.class_instance).count()
        # 해당 학급 학생들의 최근 측정 기록 수
        class_students = Student.objects.filter(school_class=ct.class_instance)
        recent_records = PAPSRecord.objects.filter(
            student_id__in=[s.id for s in class_students],
            measured_by_teacher_id=teacher_id,
            created_at__gte=datetime.now() - timedelta(days=30)
        ).count()
        
        class_info.append({
            "class": ct.class_instance,
            "role": ct.get_role_display(),
            "student_count": student_count,
            "recent_records": recent_records,
        })

    # 월별 측정 추이 데이터 (최근 6개월)
    monthly_data = []
    for i in range(6):
        target_date = datetime.now() - timedelta(days=30*i)
        month_records = PAPSRecord.objects.filter(
            measured_by_teacher_id=teacher_id,
            created_at__year=target_date.year,
            created_at__month=target_date.month
        ).count()
        monthly_data.append({
            "month": target_date.strftime("%Y-%m"),
            "count": month_records
        })
    monthly_data.reverse()

    # 종목별 측정 현황
    activity_stats = []
    activities = PAPSActivity.objects.all()
    for activity in activities[:8]:  # 상위 8개 종목만
        activity_count = PAPSRecord.objects.filter(
            measured_by_teacher_id=teacher_id,
            activity_id=activity.id
        ).count()
        activity_stats.append({
            "name": activity.get_name_display(),
            "count": activity_count
        })

    # 최근 7일 활동 데이터
    daily_activity = []
    for i in range(7):
        target_date = datetime.now().date() - timedelta(days=i)
        day_records = PAPSRecord.objects.filter(
            measured_by_teacher_id=teacher_id,
            created_at__date=target_date
        ).count()
        daily_activity.append({
            "date": target_date.strftime("%m-%d"),
            "count": day_records
        })
    daily_activity.reverse()

    # 최근 측정회차 5개 (진행률 제거)
    recent_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).order_by(
        "-created_at"
    )[:5]

    session_info = []
    for session in recent_sessions:
        # 해당 회차의 총 활동 수 (활성 상태인 것만)
        total_activities = PAPSSessionActivity.objects.filter(
            session_id=session.id,
            is_active=True
        ).count()

        # 측정 완료된 기록 수 (활성 종목에 대한 기록만)
        completed_records = PAPSRecord.objects.active_for_session(session.id).count()

        # 측정된 종목 이름들
        activity_ids = PAPSSessionActivity.objects.filter(
            session_id=session.id,
            is_active=True
        ).values_list('activity_id', flat=True)
        
        activity_names = []
        for activity_id in activity_ids:
            try:
                activity = PAPSActivity.objects.get(id=activity_id)
                activity_names.append(activity.get_name_display())
            except PAPSActivity.DoesNotExist:
                pass

        session_info.append({
            "session": session,
            "total_activities": total_activities,
            "completed_records": completed_records,
            "activity_names": activity_names[:3],  # 최대 3개만 표시
            "activity_count": len(activity_names)
        })

    context = {
        "user": request.user,
        "stats": {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "this_month_sessions": this_month_sessions,
            "total_records": total_records,
        },
        "class_info": class_info,
        "monthly_data": monthly_data,
        "activity_stats": activity_stats,
        "daily_activity": daily_activity,
        "recent_sessions": session_info,
    }
    return render(request, "physical_education/teachers/dashboard.html", context)


# ================= PAPS 측정회차 관리 =================


@login_required
@teacher_required
def paps_session_list_view(request):
    """PAPS 측정회차 목록/생성/삭제 통합 뷰"""
    teacher_id = request.user.teacher.id

    # AJAX 요청 확인
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # POST 요청 처리 (생성 또는 삭제)
    if request.method == "POST":
        # 삭제 처리
        if "delete" in request.POST:
            session_ids = request.POST.getlist("session_ids")
            if session_ids:
                deleted_count = 0
                errors = []
                for session_id in session_ids:
                    try:
                        session = PAPSSession.objects.get(
                            id=session_id, teacher_id=teacher_id
                        )
                        # 완료된 세션은 삭제 불가
                        if session.is_completed:
                            error_msg = f'완료된 측정회차 "{session.name}"는 삭제할 수 없습니다.'
                            errors.append(error_msg)
                            messages.error(request, error_msg)
                            continue
                        # 관련 측정 기록이 있는지 확인 (활성 종목에 대한 기록만)
                        if PAPSRecord.objects.active_for_session(session.id).exists():
                            error_msg = f'측정 기록이 있는 회차 "{session.name}"는 삭제할 수 없습니다.'
                            errors.append(error_msg)
                            messages.error(request, error_msg)
                            continue

                        session_name = session.name
                        session.delete()
                        deleted_count += 1
                        messages.success(
                            request, f'측정회차 "{session_name}"이 삭제되었습니다.'
                        )
                    except PAPSSession.DoesNotExist:
                        pass

                if deleted_count == 0:
                    messages.warning(request, "삭제된 측정회차가 없습니다.")

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": deleted_count > 0,
                            "deleted_count": deleted_count,
                            "errors": errors,
                        }
                    )
            else:
                messages.error(request, "삭제할 측정회차를 선택해주세요.")
                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": "삭제할 측정회차를 선택해주세요."}
                    )

        # 생성 처리
        else:
            form = PAPSSessionForm(request.POST, teacher_id=teacher_id)
            if form.is_valid():
                session = form.save()
                messages.success(
                    request, f'측정회차 "{session.name}"이 생성되었습니다.'
                )

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "session": {
                                "id": str(session.id),
                                "school_year": session.school_year,
                                "session_type": session.session_type,
                                "session_type_display": session.get_session_type_display(),
                                "name": session.name,
                                "measurement_date": session.measurement_date.strftime(
                                    "%Y-%m-%d"
                                ),
                                "is_completed": session.is_completed,
                            },
                        }
                    )
                else:
                    return redirect("physical_education:paps_session_list")
            else:
                if is_ajax:
                    return JsonResponse({"success": False, "errors": form.errors})
    else:
        form = PAPSSessionForm(teacher_id=teacher_id)

    # 필터링 파라미터
    filter_year = request.GET.get("year")
    filter_type = request.GET.get("type")

    # 세션 목록 조회
    sessions_qs = PAPSSession.objects.filter(teacher_id=teacher_id)

    # 필터링 적용
    if filter_year:
        sessions_qs = sessions_qs.filter(school_year=filter_year)
    if filter_type:
        sessions_qs = sessions_qs.filter(session_type=filter_type)

    sessions_qs = sessions_qs.order_by("-school_year", "-measurement_date")

    # AJAX 요청인 경우 JSON 응답
    if is_ajax and request.method == "GET":
        sessions_data = []
        for session in sessions_qs:
            sessions_data.append(
                {
                    "id": str(session.id),
                    "school_year": session.school_year,
                    "session_type": session.session_type,
                    "session_type_display": session.get_session_type_display(),
                    "name": session.name,
                    "measurement_date": session.measurement_date.strftime("%Y-%m-%d"),
                    "is_completed": session.is_completed,
                }
            )
        return JsonResponse(
            {"success": True, "sessions": sessions_data, "total": len(sessions_data)}
        )

    # 페이지네이션 (일반 요청의 경우)
    paginator = Paginator(sessions_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 년도 범위 생성 (현재 년도 기준 ±5년)
    current_year = timezone.now().year
    year_range = range(current_year - 5, current_year + 6)

    context = {
        "page_obj": page_obj,
        "sessions": page_obj.object_list,
        "form": form,
        "year_range": year_range,
        "current_year": current_year,
    }
    return render(
        request, "physical_education/teachers/paps/sessions/list.html", context
    )


# paps_session_create_view 제거됨 - paps_session_list_view에 통합

'''
@login_required
@teacher_required
def paps_session_create_view(request):
    """PAPS 측정회차 생성 뷰"""
    if request.method == 'POST':
        form = PAPSSessionForm(
            request.POST, 
            teacher_id=request.user.teacher.id
        )
        if form.is_valid():
            session = form.save()
            messages.success(request, f'측정회차 "{session.name}"이 생성되었습니다.')
            return redirect('physical_education:paps_session_list')
    else:
        form = PAPSSessionForm(teacher_id=request.user.teacher.id)
    
    context = {
        'form': form,
        'title': '측정회차 생성'
    }
    return render(request, 'physical_education/paps/sessions/create.html', context)
'''

# paps_session_delete_view 제거됨 - paps_session_list_view에 통합

'''
@login_required
@teacher_required
@require_POST
def paps_session_delete_view(request, session_id):
    """PAPS 측정회차 삭제 뷰"""
    session = get_object_or_404(
        PAPSSession,
        id=session_id,
        teacher_id=request.user.teacher.id
    )
    
    # 완료된 세션은 삭제 불가
    if session.is_completed:
        messages.error(request, '완료된 측정회차는 삭제할 수 없습니다.')
        return redirect('physical_education:paps_session_list')
    
    # 관련 측정 기록이 있는지 확인 (활성 종목에 대한 기록만)
    if PAPSRecord.objects.active_for_session(session.id).exists():
        messages.error(request, '측정 기록이 있는 회차는 삭제할 수 없습니다.')
        return redirect('physical_education:paps_session_list')
    
    session_name = session.name
    session.delete()
    messages.success(request, f'측정회차 "{session_name}"이 삭제되었습니다.')
    return redirect('physical_education:paps_session_list')
'''


# ================= PAPS 측정종목 선택 =================


@login_required
@teacher_required
def paps_session_activities_view(request):
    """PAPS 측정종목 선택 뷰 (렌더링 전용)"""
    # 교사의 모든 측정회차 가져오기
    sessions = PAPSSession.objects.filter(teacher_id=request.user.teacher.id).order_by(
        "-created_at"
    )

    # URL 파라미터에서 session_id 가져오기 (GET only)
    session_id = request.GET.get("session_id")
    session = None

    if session_id:
        try:
            session = get_object_or_404(
                PAPSSession, id=session_id, teacher_id=request.user.teacher.id
            )

            # 완료된 세션은 수정 불가 (경고만 표시)
            if session.is_completed:
                messages.warning(request, "완료된 측정회차는 수정할 수 없습니다.")

        except Exception:
            messages.error(request, "올바르지 않은 측정회차입니다.")
            session = None

    # 카테고리별 활동 조회 (세션이 선택된 경우에만)
    required_categories = []
    optional_categories = []
    existing_activities = []

    if session:
        required_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        ).order_by("order")

        optional_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.OPTIONAL
        ).order_by("order")

        # 기존 선택된 종목들 조회 (활성 상태인 것만)
        existing_activities = PAPSSessionActivity.objects.filter(
            session_id=session.id,
            is_active=True
        ).select_related("category_id", "activity_id")

    context = {
        "sessions": sessions,
        "session": session,
        "existing_activities": existing_activities,
        "required_categories": required_categories,
        "optional_categories": optional_categories,
        "grade_choices": PAPSSessionActivity.GRADE_CHOICES,
    }
    return render(
        request,
        "physical_education/teachers/paps/sessions/session_activities.html",
        context,
    )


# ================= PAPS 측정 입력 =================


@login_required
@teacher_required
def paps_required_measurement_view(request):
    """PAPS 필수평가 측정 입력 뷰"""
    teacher_id = request.user.teacher.id

    # 필수평가 카테고리 조회
    required_categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.REQUIRED
    ).order_by("order")

    # 교사의 측정회차 목록 조회
    available_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).order_by(
        "-created_at"
    )

    # 교사가 담당하는 학급들 조회 (ClassTeacher 모델 기반)
    teacher_classes = (
        ClassTeacher.objects.filter(teacher_id=teacher_id)
        .select_related("class_instance")
        .order_by("class_instance__grade", "class_instance__class_number")
    )

    # 교사가 담당하는 실제 학년 목록 추출 (중복 제거, PAPS 대상만)
    paps_grades = set()
    for ct in teacher_classes:
        grade = ct.class_instance.grade
        if 4 <= grade <= 12:  # PAPS 대상: 초4~고3
            paps_grades.add(grade)

    # 학년 선택지 생성 (실제 담당 학년만)
    grade_choices = [
        (grade, get_grade_display_name(grade)) for grade in sorted(paps_grades)
    ]

    # 교사가 담당하는 실제 학급 목록 생성
    available_classes = []
    for ct in teacher_classes:
        cls = ct.class_instance
        if 4 <= cls.grade <= 12:  # PAPS 대상만
            available_classes.append(
                {
                    "id": cls.id,
                    "name": f"{cls.class_number}반",
                    "full_name": f"{cls.grade}학년 {cls.class_number}반",
                    "grade": cls.grade,
                    "class_number": cls.class_number,
                    "role": ct.get_role_display(),
                }
            )

    # 년도 범위 생성 (현재 년도 기준 ±5년)
    current_year = timezone.now().year
    year_range = range(current_year - 5, current_year + 6)

    # 필수평가 카테고리 JSON 직렬화를 위한 처리
    categories_json = []
    for category in required_categories:
        categories_json.append(
            {
                "id": str(category.id),
                "name": category.name,
                "display_name": category.get_name_display(),
                "evaluation_type": category.evaluation_type,
                "order": category.order,
            }
        )

    # 측정회차 JSON 직렬화를 위한 처리
    sessions_json = []
    for session in available_sessions:
        sessions_json.append(
            {
                "id": str(session.id),
                "name": session.name,
                "school_year": session.school_year,
                "session_type": session.session_type,
                "session_type_display": session.get_session_type_display(),
                "measurement_date": session.measurement_date.strftime("%Y-%m-%d"),
                "is_completed": session.is_completed,
            }
        )

    context = {
        "required_categories": required_categories,
        "available_sessions": available_sessions,
        "available_classes": available_classes,
        "grade_choices": grade_choices,
        "year_range": year_range,
        "current_year": current_year,
        "evaluation_type": "required",
        "title": "PAPS 필수평가 입력",
        # JavaScript에서 사용할 JSON 데이터
        "required_categories_json": json.dumps(categories_json),
        "available_sessions_json": json.dumps(sessions_json),
        "available_classes_json": json.dumps(available_classes),
        "grade_choices_json": json.dumps(grade_choices),
    }
    return render(
        request, "physical_education/teachers/paps/measurement/required.html", context
    )


@login_required
@teacher_required
def paps_optional_measurement_view(request):
    """PAPS 선택평가 측정 입력 뷰"""
    teacher_id = request.user.teacher.id
    
    # 선택평가 카테고리 조회
    optional_categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.OPTIONAL
    ).order_by("order")
    
    # 교사의 측정회차 목록 조회
    available_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).order_by(
        "-created_at"
    )
    
    # 교사가 담당하는 학급들 조회 (ClassTeacher 모델 기반)
    teacher_classes = (
        ClassTeacher.objects.filter(teacher_id=teacher_id)
        .select_related("class_instance")
        .order_by("class_instance__grade", "class_instance__class_number")
    )
    
    # 교사가 담당하는 실제 학년 목록 추출 (중복 제거, PAPS 대상만)
    paps_grades = set()
    for ct in teacher_classes:
        grade = ct.class_instance.grade
        if 4 <= grade <= 12:  # PAPS 대상: 초4~고3
            paps_grades.add(grade)
    
    # 학년 선택지 생성 (실제 담당 학년만)
    grade_choices = [
        (grade, get_grade_display_name(grade)) for grade in sorted(paps_grades)
    ]
    
    # 현재 연도 기준으로 학년도 범위 생성 (현재년도 ± 2년)
    current_year = timezone.now().year
    year_range = list(range(current_year - 2, current_year + 3))
    
    # 학급 정보 JSON 직렬화
    available_classes = []
    for ct in teacher_classes:
        available_classes.append(
            {
                "id": ct.class_instance.id,
                "name": f"{ct.class_instance.grade}학년 {ct.class_instance.class_number}반",
                "grade": ct.class_instance.grade,
                "class_number": ct.class_instance.class_number,
            }
        )
    
    # 선택평가 카테고리 JSON 직렬화
    optional_categories_json = []
    for category in optional_categories:
        optional_categories_json.append(
            {
                "id": str(category.id),
                "name": category.name,
                "name_display": category.get_name_display(),
                "order": category.order,
                "evaluation_type": category.evaluation_type,
            }
        )
    
    context = {
        "current_year": current_year,
        "year_range": year_range,
        "grade_choices": grade_choices,
        "grade_choices_json": json.dumps(grade_choices),
        "available_classes": available_classes,
        "available_classes_json": json.dumps(available_classes),
        "available_sessions": available_sessions,
        "available_sessions_json": json.dumps(
            [
                {
                    "id": str(session.id),
                    "name": session.name,
                    "school_year": session.school_year,
                    "session_type": session.session_type,
                    "measurement_date": session.measurement_date.strftime("%Y-%m-%d"),
                    "is_completed": session.is_completed,
                }
                for session in available_sessions
            ]
        ),
        "optional_categories": optional_categories,
        "optional_categories_json": json.dumps(optional_categories_json),
    }
    
    return render(
        request, "physical_education/teachers/paps/measurement/optional.html", context
    )


# ================= PAPS API 엔드포인트 =================


@login_required
@teacher_required
@require_POST
@csrf_exempt
def api_paps_save_measurement(request):
    """PAPS 측정 데이터 저장 API"""
    try:
        data = json.loads(request.body)

        session_id = data.get("session_id")
        student_id = data.get("student_id")
        activity_id = data.get("activity_id")
        measurement_data = data.get("measurement_data", {})

        # 유효성 검사
        if not all([session_id, student_id, activity_id]):
            return JsonResponse(
                {"success": False, "error": "필수 파라미터가 누락되었습니다."}
            )

        # 권한 확인
        session = get_object_or_404(
            PAPSSession, id=session_id, teacher_id=request.user.teacher.id
        )

        activity = get_object_or_404(PAPSActivity, id=activity_id)

        # 학생 정보 확인 및 권한 검증
        try:
            student = get_object_or_404(Student, id=student_id)
            class_id = student.school_class.id
            student_grade = student.school_class.grade
            
            # 교사가 해당 학생의 학급을 담당하는지 권한 확인
            if not ClassTeacher.objects.filter(
                teacher_id=request.user.teacher.id, 
                class_instance=student.school_class
            ).exists():
                return JsonResponse(
                    {"success": False, "error": "해당 학생의 측정 데이터를 저장할 권한이 없습니다."}
                )
        except Student.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "해당 학생을 찾을 수 없습니다."}
            )

        # 기존 기록 조회 및 업데이트 (PAPSRecord는 PAPSSessionActivity 생성 시 자동 생성됨)
        try:
            record = PAPSRecord.objects.get(
                session_id=session.id,
                student_id=student_id,
                activity_id=activity.id
            )
        except PAPSRecord.DoesNotExist:
            return JsonResponse({
                "success": False, 
                "error": "측정 기록을 찾을 수 없습니다. 측정 종목이 올바르게 설정되었는지 확인해주세요."
            })

        # 측정 데이터 자동 계산 처리 추가
        from .utils import process_measurement_data
        processed_data = process_measurement_data(
            activity.name,
            measurement_data,
            student_grade
        )
        
        # 등급 계산 및 저장
        evaluation_grade = None
        if activity.evaluation_criteria:
            grade_result = calculate_paps_grade(activity, processed_data, student_grade)
            if 'error' not in grade_result:
                # 임시로 male_grade를 사용 (실제로는 학생 성별에 따라 결정)
                if grade_result.get('male_grade_code'):
                    grade_code = grade_result.get('male_grade_code')
                    # grade_code가 'grade_1', 'grade_2' 등의 형태일 때 숫자만 추출
                    if grade_code and grade_code.startswith('grade_'):
                        try:
                            evaluation_grade = int(grade_code.split('_')[1])
                        except (IndexError, ValueError):
                            pass
        
        # 측정 데이터 업데이트 (계산된 값 포함)
        record.measurement_data = processed_data
        record.evaluation_grade = evaluation_grade
        record.measured_at = timezone.now()
        record.save()

        # BMI 저장 시 체지방률평가로 데이터 동기화
        if activity.name == 'BMI':
            from .utils import BMI_TO_BODY_FAT_FIELD_MAP
            try:
                # 체지방률평가 Activity 조회
                body_fat_activity = PAPSActivity.objects.filter(name='BODY_FAT_RATE_TEST').first()
                if body_fat_activity:
                    # 동일 session의 체지방률평가 PAPSRecord 조회
                    body_fat_record = PAPSRecord.objects.filter(
                        session_id=session.id,
                        student_id=student_id,
                        activity_id=body_fat_activity.id
                    ).first()
                    
                    if body_fat_record:
                        # BMI 데이터를 체지방률평가로 복사
                        updated = False
                        for bmi_field, body_fat_field in BMI_TO_BODY_FAT_FIELD_MAP.items():
                            bmi_value = processed_data.get(bmi_field)
                            if bmi_value is not None:
                                body_fat_record.measurement_data[body_fat_field] = bmi_value
                                updated = True
                        
                        if updated:
                            body_fat_record.save()
                            
            except Exception as sync_error:
                # 동기화 실패는 로그만 남기고 메인 처리는 성공으로 처리
                print(f"BMI 동기화 실패: {sync_error}")

        return JsonResponse(
            {
                "success": True, 
                "record_id": str(record.id), 
                "updated": True,
                "measurement_data": record.measurement_data,  # DB에 저장된 실제 측정 데이터
                "evaluation_grade": record.evaluation_grade   # 계산된 등급 (1-5 또는 None)
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "JSON 데이터가 올바르지 않습니다."}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})



@login_required
@teacher_required
def api_paps_get_activities(request, category):
    """카테고리별 PAPS 활동 목록 API"""
    try:
        # UUID 형태인지 확인 후 ID로 검색, 아니면 name으로 검색
        import uuid
        try:
            uuid.UUID(category)  # UUID 유효성 검사
            category_obj = get_object_or_404(PAPSCategory, id=category)
        except ValueError:
            # UUID가 아니면 name으로 검색 (하위 호환성)
            category_obj = get_object_or_404(PAPSCategory, name=category)
        
        activities = PAPSActivity.objects.filter(category_id=category_obj.id)

        activities_data = []
        for activity in activities:
            activities_data.append(
                {
                    "id": str(activity.id),
                    "name": activity.name,  # English code for buildColumns lookup
                    "display_name": activity.get_name_display(),  # Korean name for UI display
                    "measurement_schema": activity.measurement_schema,
                    "evaluation_criteria": activity.evaluation_criteria,
                }
            )

        return JsonResponse({"success": True, "activities": activities_data})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_get_students_by_class(request):
    """학급별 학생 목록 조회 API"""
    try:
        teacher_id = request.user.teacher.id
        year = request.GET.get("year")
        grade = request.GET.get("grade")
        class_id = request.GET.get("class")

        if not all([year, grade, class_id]):
            return JsonResponse(
                {"success": False, "error": "년도, 학년, 학급 정보가 필요합니다."}
            )

        # 해당 학급이 존재하는지 확인
        try:
            class_instance = Class.objects.get(id=class_id, grade=grade)
        except Class.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "해당 학급을 찾을 수 없습니다."}
            )

        # 교사가 해당 학급을 담당하는지 권한 확인
        if not ClassTeacher.objects.filter(
            teacher_id=teacher_id, class_instance=class_instance
        ).exists():
            return JsonResponse(
                {"success": False, "error": "해당 학급에 대한 권한이 없습니다."}
            )

        # 해당 학급의 실제 학생 데이터 조회
        students = Student.objects.filter(school_class=class_instance).select_related(
            "user"
        ).order_by("student_id")

        # JSON 응답용 학생 데이터 구성
        students_data = []
        for idx, student in enumerate(students, 1):
            students_data.append(
                {
                    "id": student.id,
                    "name": get_korean_name(student.user),
                    "number": get_student_number_from_id(student.student_id),
                    "gender": get_student_gender(student),
                    "student_id": student.student_id,
                    "birth_date": (
                        student.birth_date.strftime("%Y-%m-%d")
                        if student.birth_date
                        else None
                    ),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "students": students_data,
                "total": len(students_data),
                "class_info": {
                    "year": int(year),
                    "grade": int(grade),
                    "class_id": int(class_id),
                    "class_name": f"{class_instance.grade}학년 {class_instance.class_number}반",
                    "school_name": class_instance.school.name,
                },
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"학생 목록 조회 중 오류: {str(e)}"}
        )


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_paps_get_measurements_by_activity(request):
    """특정 활동에 대한 학생별 측정 기록 조회 API"""
    try:
        teacher_id = request.user.teacher.id
        session_id = request.GET.get("session_id")
        activity_id = request.GET.get("activity_id")
        class_id = request.GET.get("class_id")
        grade = request.GET.get("grade")
        
        if not all([session_id, activity_id, class_id, grade]):
            return JsonResponse(
                {"success": False, "error": "필수 파라미터가 누락되었습니다."}
            )
            
        # 권한 확인 - 해당 측정회차가 교사 소유인지
        session = get_object_or_404(
            PAPSSession, id=session_id, teacher_id=teacher_id
        )
        
        # 학급 권한 확인
        try:
            class_instance = Class.objects.get(id=class_id, grade=grade)
        except Class.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "해당 학급을 찾을 수 없습니다."}
            )
            
        if not ClassTeacher.objects.filter(
            teacher_id=teacher_id, class_instance=class_instance
        ).exists():
            return JsonResponse(
                {"success": False, "error": "해당 학급에 대한 권한이 없습니다."}
            )
        
        # 해당 학급의 학생 목록 조회
        students = Student.objects.filter(school_class=class_instance).select_related(
            "user"
        ).order_by("student_id")
        
        # 해당 활동에 대한 측정 기록들 조회
        records = PAPSRecord.objects.filter(
            session_id=session_id,
            activity_id=activity_id,
            class_id=class_id,
            student_grade=grade
        ).select_related()
        
        # 학생별 측정 기록 매핑
        records_by_student = {record.student_id: record for record in records}
        
        # 학생 데이터와 측정 기록을 결합
        students_data = []
        for student in students:
            record = records_by_student.get(student.id)
            measurement_data = record.measurement_data if record else {}
            
            student_data = {
                "id": student.id,
                "name": get_korean_name(student.user),
                "number": get_student_number_from_id(student.student_id),
                "gender": get_student_gender(student),
                "student_id": student.student_id,
                "measurement_data": measurement_data,
                "evaluation_grade": record.evaluation_grade if record else None,
                "measured_at": record.measured_at.isoformat() if record and record.measured_at else None,
                "notes": record.notes if record else "",
                "record_id": str(record.id) if record else None
            }
            students_data.append(student_data)
        
        return JsonResponse(
            {
                "success": True,
                "students": students_data,
                "total": len(students_data),
                "activity_info": {
                    "session_id": session_id,
                    "activity_id": activity_id,
                    "class_id": int(class_id),
                    "grade": int(grade)
                },
                "records_count": len(records)
            }
        )
        
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"측정 기록 조회 중 오류: {str(e)}"}
        )


# ==================== PAPS 통계 뷰 ====================

@login_required
@teacher_required
def activity_average_view(request):
    """종목별 평균 기록 페이지 (SSR)"""
    teacher = request.user.teacher
    
    # 담당 학급 조회
    teacher_classes = ClassTeacher.objects.filter(
        teacher=teacher
    ).select_related('class_instance', 'class_instance__school')
    
    # 종목 목록 조회 (필수평가만)
    activities = PAPSActivity.objects.filter(
        category_id__in=PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        ).values_list('id', flat=True)
    ).order_by('name')
    
    # 담당 학급의 학년 목록
    grades = set()
    classes_data = []
    for tc in teacher_classes:
        grades.add(tc.class_instance.grade)
        classes_data.append({
            'id': tc.class_instance.id,
            'name': f"{tc.class_instance.grade}학년 {tc.class_instance.class_number}반",
            'grade': tc.class_instance.grade,
        })
    
    # 종목 데이터 구성
    activities_data = []
    for activity in activities:
        activities_data.append({
            'id': str(activity.id),
            'name': activity.name,
            'display_name': get_activity_display_name(activity.name),
            'unit': get_activity_unit(activity.name),
        })
    
    # 학년별 데이터 구성
    grades_data = []
    for grade in sorted(grades):
        grades_data.append({
            'value': grade,
            'display': get_grade_from_number(grade),
        })
    
    context = {
        'activities': activities_data,
        'grades': grades_data,
        'classes': classes_data,
    }
    
    return render(request, 'physical_education/teachers/statistics/activity/average.html', context)


@login_required
@teacher_required
def grade_distribution_view(request):
    """등급 분포 현황 페이지 (SSR)"""
    teacher = request.user.teacher
    
    # 담당 학급 조회
    teacher_classes = ClassTeacher.objects.filter(
        teacher=teacher
    ).select_related('class_instance', 'class_instance__school')
    
    # 종목 목록 조회 (필수평가만)
    activities = PAPSActivity.objects.filter(
        category_id__in=PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        ).values_list('id', flat=True)
    ).order_by('name')
    
    # 담당 학급의 학년 목록
    grades = set()
    classes_data = []
    for tc in teacher_classes:
        grades.add(tc.class_instance.grade)
        classes_data.append({
            'id': tc.class_instance.id,
            'name': f"{tc.class_instance.grade}학년 {tc.class_instance.class_number}반",
            'grade': tc.class_instance.grade,
        })
    
    # 종목 데이터 구성
    activities_data = []
    for activity in activities:
        activities_data.append({
            'id': str(activity.id),
            'name': activity.name,
            'display_name': get_activity_display_name(activity.name),
            'unit': get_activity_unit(activity.name),
        })
    
    # 학년별 데이터 구성
    grades_data = []
    for grade in sorted(grades):
        grades_data.append({
            'value': grade,
            'display': get_grade_from_number(grade),
        })
    
    context = {
        'activities': activities_data,
        'grades': grades_data,
        'classes': classes_data,
    }
    
    return render(request, 'physical_education/teachers/statistics/activity/grade_distribution.html', context)


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_activity_average(request):
    """종목별 평균 기록 데이터 API"""
    try:
        teacher = request.user.teacher
        activity_id = request.GET.get('activity_id')
        grade_filter = request.GET.get('grade')
        gender_filter = request.GET.get('gender', 'M')  # 기본값: 남성
        
        if not activity_id:
            return JsonResponse({
                'success': False, 
                'error': '종목을 선택해주세요.'
            })
        
        # 종목 정보 조회
        try:
            activity = PAPSActivity.objects.get(id=activity_id)
        except PAPSActivity.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '종목을 찾을 수 없습니다.'
            })
        
        # 담당 학급 조회
        teacher_classes = ClassTeacher.objects.filter(
            teacher=teacher
        ).values_list('class_instance_id', flat=True)
        
        # 활성화된 PAPSSessionActivity의 session_id들 조회
        active_sessions = PAPSSessionActivity.objects.filter(
            activity_id=activity_id,
            is_active=True
        ).values_list('session_id', flat=True).distinct()
        
        # 기본 쿼리셋 구성 (활성 종목에 대한 기록만)
        records_query = PAPSRecord.objects.filter(
            activity_id=activity_id,
            evaluation_grade__isnull=False,  # 완전한 측정 기록만
            class_id__in=teacher_classes,
            session_id__in=active_sessions  # 활성 종목만
        )
        
        # 학년 필터 적용
        if grade_filter and grade_filter != 'all':
            # Class를 통해 학년 필터링
            grade_classes = Class.objects.filter(
                id__in=teacher_classes,
                grade=int(grade_filter)
            ).values_list('id', flat=True)
            records_query = records_query.filter(class_id__in=grade_classes)
        
        # 데이터 처리
        records = list(records_query)
        
        if not records:
            return JsonResponse({
                'success': True,
                'data': {
                    'activity_name': get_activity_display_name(activity.name),
                    'unit': get_activity_unit(activity.name),
                    'grade_averages': [],
                    'distribution': [],
                    'statistics': {
                        'total_count': 0,
                        'average': 0,
                        'min': 0,
                        'max': 0,
                        'std_dev': 0
                    }
                }
            })
        
        # 측정값 추출 및 유효한 데이터만 필터링
        valid_records = []
        for record in records:
            value = get_measurement_value(activity.name, record.measurement_data)
            if value is not None:
                # Class 정보 조회 (학년 정보를 위해)
                try:
                    class_obj = Class.objects.get(id=record.class_id)
                    valid_records.append({
                        'value': value,
                        'grade': class_obj.grade,
                        'evaluation_grade': record.evaluation_grade,
                    })
                except Class.DoesNotExist:
                    continue
        
        if not valid_records:
            return JsonResponse({
                'success': True,
                'data': {
                    'activity_name': get_activity_display_name(activity.name),
                    'unit': get_activity_unit(activity.name),
                    'grade_averages': [],
                    'distribution': [],
                    'statistics': {
                        'total_count': 0,
                        'average': 0,
                        'min': 0,
                        'max': 0,
                        'std_dev': 0
                    }
                }
            })
        
        # 학년별 평균 계산
        from collections import defaultdict
        import statistics
        
        grade_data = defaultdict(list)
        all_values = []
        
        for record in valid_records:
            grade_data[record['grade']].append(record['value'])
            all_values.append(record['value'])
        
        # 학년별 평균 데이터 구성
        grade_averages = []
        for grade in sorted(grade_data.keys()):
            values = grade_data[grade]
            grade_averages.append({
                'grade': grade,
                'grade_display': get_grade_from_number(grade),
                'average': round(statistics.mean(values), 2),
                'count': len(values)
            })
        
        # 분포 데이터 생성 (히스토그램용)
        min_val = min(all_values)
        max_val = max(all_values)
        range_size = (max_val - min_val) / 10  # 10개 구간
        
        distribution = []
        for i in range(10):
            range_start = min_val + (range_size * i)
            range_end = min_val + (range_size * (i + 1))
            count = sum(1 for v in all_values if range_start <= v < range_end)
            if i == 9:  # 마지막 구간은 최댓값 포함
                count = sum(1 for v in all_values if range_start <= v <= range_end)
            
            distribution.append({
                'range': f"{range_start:.1f}-{range_end:.1f}",
                'count': count
            })
        
        # 전체 통계
        stats = {
            'total_count': len(all_values),
            'average': round(statistics.mean(all_values), 2),
            'min': round(min_val, 2),
            'max': round(max_val, 2),
            'std_dev': round(statistics.stdev(all_values) if len(all_values) > 1 else 0, 2)
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'activity_name': get_activity_display_name(activity.name),
                'unit': get_activity_unit(activity.name),
                'grade_averages': grade_averages,
                'distribution': distribution,
                'statistics': stats
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 처리 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_grade_distribution(request):
    """등급 분포 현황 데이터 API"""
    try:
        teacher = request.user.teacher
        activity_id = request.GET.get('activity_id')
        grade_filter = request.GET.get('grade')
        gender_filter = request.GET.get('gender', 'M')  # 기본값: 남성
        
        if not activity_id:
            return JsonResponse({
                'success': False, 
                'error': '종목을 선택해주세요.'
            })
        
        # 종목 정보 조회
        try:
            activity = PAPSActivity.objects.get(id=activity_id)
        except PAPSActivity.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '종목을 찾을 수 없습니다.'
            })
        
        # 담당 학급 조회
        teacher_classes = ClassTeacher.objects.filter(
            teacher=teacher
        ).values_list('class_instance_id', flat=True)
        
        # 활성화된 PAPSSessionActivity의 session_id들 조회
        active_sessions = PAPSSessionActivity.objects.filter(
            activity_id=activity_id,
            is_active=True
        ).values_list('session_id', flat=True).distinct()
        
        # 기본 쿼리셋 구성 (활성 종목의 등급이 있는 완전한 측정 기록만)
        records_query = PAPSRecord.objects.filter(
            activity_id=activity_id,
            evaluation_grade__isnull=False,  # 완전한 측정 기록만
            class_id__in=teacher_classes,
            session_id__in=active_sessions  # 활성 종목만
        )
        
        # 학년 필터 적용
        if grade_filter and grade_filter != 'all':
            # Class를 통해 학년 필터링
            grade_classes = Class.objects.filter(
                id__in=teacher_classes,
                grade=int(grade_filter)
            ).values_list('id', flat=True)
            records_query = records_query.filter(class_id__in=grade_classes)
        
        # 데이터 처리
        records = list(records_query)
        
        if not records:
            return JsonResponse({
                'success': True,
                'data': {
                    'activity_name': get_activity_display_name(activity.name),
                    'grade_distribution': [],
                    'overall_distribution': {},
                    'statistics': {
                        'total_count': 0,
                        'average_grade': 0,
                        'mode_grade': 0
                    }
                }
            })
        
        # 학년별 등급 분포 계산
        from collections import defaultdict
        import statistics
        
        grade_data = defaultdict(lambda: defaultdict(int))
        all_grades = []
        
        for record in records:
            # Class 정보 조회 (학년 정보를 위해)
            try:
                class_obj = Class.objects.get(id=record.class_id)
                student_grade = class_obj.grade
                evaluation_grade = record.evaluation_grade
                
                grade_data[student_grade][evaluation_grade] += 1
                all_grades.append(evaluation_grade)
                
            except Class.DoesNotExist:
                continue
        
        if not all_grades:
            return JsonResponse({
                'success': True,
                'data': {
                    'activity_name': get_activity_display_name(activity.name),
                    'grade_distribution': [],
                    'overall_distribution': {},
                    'statistics': {
                        'total_count': 0,
                        'average_grade': 0,
                        'mode_grade': 0
                    }
                }
            })
        
        # 학년별 분포 데이터 구성
        grade_distribution = []
        for student_grade in sorted(grade_data.keys()):
            distribution = grade_data[student_grade]
            total_for_grade = sum(distribution.values())
            
            grade_distribution.append({
                'grade': student_grade,
                'grade_display': get_grade_from_number(student_grade),
                'distribution': {
                    'grade_1': distribution.get(1, 0),
                    'grade_2': distribution.get(2, 0),
                    'grade_3': distribution.get(3, 0),
                    'grade_4': distribution.get(4, 0),
                    'grade_5': distribution.get(5, 0),
                },
                'total': total_for_grade
            })
        
        # 전체 등급 분포 계산
        overall_counts = defaultdict(int)
        for grade in all_grades:
            overall_counts[grade] += 1
        
        total_count = len(all_grades)
        overall_distribution = {}
        for i in range(1, 6):  # 1등급~5등급
            count = overall_counts.get(i, 0)
            percentage = (count / total_count * 100) if total_count > 0 else 0
            overall_distribution[f'grade_{i}'] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        
        # 통계 계산
        average_grade = round(statistics.mean(all_grades), 2) if all_grades else 0
        mode_grade = statistics.mode(all_grades) if all_grades else 0
        
        return JsonResponse({
            'success': True,
            'data': {
                'activity_name': get_activity_display_name(activity.name),
                'grade_distribution': grade_distribution,
                'overall_distribution': overall_distribution,
                'statistics': {
                    'total_count': total_count,
                    'average_grade': average_grade,
                    'mode_grade': mode_grade
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 처리 중 오류가 발생했습니다: {str(e)}'
        })


# ================= 개인별 통계 뷰 =================

@login_required
@teacher_required
def individual_profile_view(request):
    """학생 개인 프로필 페이지 (SSR)"""
    teacher = request.user.teacher
    
    # 담당 학급 조회
    teacher_classes = ClassTeacher.objects.filter(
        teacher=teacher
    ).select_related('class_instance', 'class_instance__school')
    
    # 담당 학급 목록
    classes = []
    for tc in teacher_classes:
        classes.append({
            'id': tc.class_instance.id,
            'name': tc.class_instance.name,
            'grade': tc.class_instance.grade,
            'grade_display': get_grade_display_name(tc.class_instance.grade)
        })
    
    # 학년도 목록 (측정회차가 있는 학년도만)
    school_years = PAPSSession.objects.filter(
        teacher_id=teacher.id
    ).values_list('school_year', flat=True).distinct().order_by('-school_year')
    
    # 측정회차 목록
    sessions = PAPSSession.objects.filter(
        teacher_id=teacher.id,
        is_active=True
    ).order_by('-school_year', '-measurement_date')
    
    context = {
        'classes': classes,
        'school_years': list(school_years),
        'sessions': sessions,
    }
    
    return render(request, 'physical_education/teachers/statistics/individual/profile.html', context)


@login_required
@teacher_required  
def individual_growth_view(request):
    """종목별 성장 추이 페이지 (SSR)"""
    teacher = request.user.teacher
    
    # 담당 학급 조회
    teacher_classes = ClassTeacher.objects.filter(
        teacher=teacher
    ).select_related('class_instance', 'class_instance__school')
    
    # 담당 학급 목록
    classes = []
    for tc in teacher_classes:
        classes.append({
            'id': tc.class_instance.id,
            'name': tc.class_instance.name,
            'grade': tc.class_instance.grade,
            'grade_display': get_grade_display_name(tc.class_instance.grade)
        })
    
    # 종목 목록 조회 (필수평가만)
    activities = PAPSActivity.objects.filter(
        category_id__in=PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        ).values_list('id', flat=True)
    ).order_by('name')
    
    # 활동 목록 변환
    activity_list = []
    for activity in activities:
        activity_list.append({
            'id': str(activity.id),
            'display_name': get_activity_display_name(activity.name),
            'unit': get_activity_unit(activity.name)
        })
    
    # 학년도 목록
    school_years = PAPSSession.objects.filter(
        teacher_id=teacher.id
    ).values_list('school_year', flat=True).distinct().order_by('-school_year')
    
    context = {
        'classes': classes,
        'activities': activity_list,
        'school_years': list(school_years),
    }
    
    return render(request, 'physical_education/teachers/statistics/individual/growth.html', context)


@login_required
@teacher_required
def api_individual_profile(request):
    """학생 개인 프로필 데이터 API"""
    try:
        teacher = request.user.teacher
        student_id = request.GET.get('student_id')
        session_id = request.GET.get('session_id')
        compare_mode = request.GET.get('compare_mode', 'false') == 'true'
        
        if not student_id:
            return JsonResponse({
                'success': False,
                'error': '학생을 선택해주세요.'
            })
        
        # 학생 정보 조회 및 권한 확인
        try:
            student = Student.objects.select_related('user', 'school_class').get(id=student_id)
            # 담당 학급 확인
            teacher_classes = ClassTeacher.objects.filter(
                teacher=teacher,
                class_instance=student.school_class
            ).exists()
            
            if not teacher_classes:
                return JsonResponse({
                    'success': False,
                    'error': '해당 학생에 대한 조회 권한이 없습니다.'
                })
                
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '학생을 찾을 수 없습니다.'
            })
        
        # 세션 선택 (기본값: 최신 세션)
        if not session_id:
            latest_session = PAPSSession.objects.filter(
                teacher_id=teacher.id,
                is_active=True
            ).order_by('-school_year', '-measurement_date').first()
            
            if not latest_session:
                return JsonResponse({
                    'success': False,
                    'error': '측정 회차가 없습니다.'
                })
            session_id = str(latest_session.id)
        
        # 세션 정보 조회
        try:
            session = PAPSSession.objects.get(id=session_id, teacher_id=teacher.id)
        except PAPSSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '측정 회차를 찾을 수 없습니다.'
            })
        
        # 해당 세션의 활성화된 종목들 조회
        active_activity_ids = PAPSSessionActivity.objects.filter(
            session_id=session_id,
            is_active=True
        ).values_list('activity_id', flat=True)
        
        # 학생의 측정 기록 조회 (활성 종목만)
        records = PAPSRecord.objects.filter(
            session_id=session_id,
            student_id=student_id,
            activity_id__in=active_activity_ids,  # 활성 종목만
            evaluation_grade__isnull=False  # 완전한 측정 기록만
        ).select_related()
        
        # 체력요인별 데이터 수집
        category_data = {}
        activities_data = []
        
        # 5개 체력요인 초기화
        categories = ['심폐지구력', '유연성', '근력/근지구력', '순발력', '비만']
        radar_data = {
            'categories': categories,
            'grades': [0, 0, 0, 0, 0]  # 미측정은 0
        }
        
        # 기록 처리
        for record in records:
            try:
                activity = PAPSActivity.objects.get(id=record.activity_id)
                category = PAPSCategory.objects.get(id=activity.category_id)
                
                # 카테고리별 등급 설정
                category_name = category.get_name_display()
                if category_name in categories:
                    idx = categories.index(category_name)
                    radar_data['grades'][idx] = record.evaluation_grade
                
                # 활동 데이터 추가
                measurement_value = get_measurement_value(activity.name, record.measurement_data)
                activities_data.append({
                    'activity': get_activity_display_name(activity.name),
                    'category': category_name,
                    'value': measurement_value,
                    'unit': get_activity_unit(activity.name),
                    'grade': record.evaluation_grade,
                    'measured_at': record.measured_at.strftime('%Y-%m-%d %H:%M') if record.measured_at else None
                })
                
            except (PAPSActivity.DoesNotExist, PAPSCategory.DoesNotExist):
                continue
        
        # 최근 측정 히스토리 (최근 5개, 활성 종목만)
        # 모든 활성 종목 ID들 조회
        all_active_activity_ids = PAPSSessionActivity.objects.filter(
            is_active=True
        ).values_list('activity_id', flat=True).distinct()
        
        recent_records = PAPSRecord.objects.filter(
            student_id=student_id,
            activity_id__in=all_active_activity_ids,  # 활성 종목만
            evaluation_grade__isnull=False
        ).order_by('-measured_at')[:5]
        
        recent_history = []
        for record in recent_records:
            try:
                activity = PAPSActivity.objects.get(id=record.activity_id)
                session_info = PAPSSession.objects.get(id=record.session_id)
                
                measurement_value = get_measurement_value(activity.name, record.measurement_data)
                recent_history.append({
                    'session_name': session_info.name,
                    'activity': get_activity_display_name(activity.name),
                    'value': measurement_value,
                    'unit': get_activity_unit(activity.name),
                    'grade': record.evaluation_grade,
                    'measured_at': record.measured_at.strftime('%Y-%m-%d') if record.measured_at else None
                })
            except (PAPSActivity.DoesNotExist, PAPSSession.DoesNotExist):
                continue
        
        # 통계 계산
        grades = [g for g in radar_data['grades'] if g > 0]
        statistics_data = {
            'average_grade': round(sum(grades) / len(grades), 1) if grades else 0,
            'completion_rate': len(grades) / 5 * 100,  # 5개 요인 대비 완료율
            'measurement_count': len(activities_data)
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'student_info': {
                    'id': student.id,
                    'name': get_korean_name(student.user),
                    'class': student.school_class.name,
                    'grade': student.school_class.grade,
                    'grade_display': get_grade_display_name(student.school_class.grade)
                },
                'session_data': {
                    'session_id': str(session.id),
                    'session_name': session.name,
                    'measurement_date': session.measurement_date.strftime('%Y-%m-%d'),
                    'radar_data': radar_data,
                    'records': activities_data
                },
                'recent_history': recent_history,
                'statistics': statistics_data
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 처리 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
def api_individual_growth(request):
    """종목별 성장 추이 데이터 API"""
    try:
        teacher = request.user.teacher
        student_id = request.GET.get('student_id')
        activity_id = request.GET.get('activity_id')
        school_year = request.GET.get('school_year')
        
        if not student_id or not activity_id:
            return JsonResponse({
                'success': False,
                'error': '학생과 종목을 선택해주세요.'
            })
        
        # 학생 정보 조회 및 권한 확인
        try:
            student = Student.objects.select_related('user', 'school_class').get(id=student_id)
            # 담당 학급 확인
            teacher_classes = ClassTeacher.objects.filter(
                teacher=teacher,
                class_instance=student.school_class
            ).exists()
            
            if not teacher_classes:
                return JsonResponse({
                    'success': False,
                    'error': '해당 학생에 대한 조회 권한이 없습니다.'
                })
                
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '학생을 찾을 수 없습니다.'
            })
        
        # 활동 정보 조회
        try:
            activity = PAPSActivity.objects.get(id=activity_id)
        except PAPSActivity.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '종목을 찾을 수 없습니다.'
            })
        
        # 해당 종목의 활성화된 세션들 조회  
        active_sessions = PAPSSessionActivity.objects.filter(
            activity_id=activity_id,
            is_active=True
        ).values_list('session_id', flat=True).distinct()
        
        # 기본 쿼리 (해당 학생의 해당 종목 기록, 활성 종목만)
        records_query = PAPSRecord.objects.filter(
            student_id=student_id,
            activity_id=activity_id,
            session_id__in=active_sessions,  # 활성 종목만
            evaluation_grade__isnull=False  # 완전한 측정 기록만
        )
        
        # 학년도 필터
        if school_year:
            sessions = PAPSSession.objects.filter(
                teacher_id=teacher.id,
                school_year=int(school_year)
            ).values_list('id', flat=True)
            records_query = records_query.filter(session_id__in=sessions)
        
        # 기록 조회 및 정렬
        records = records_query.select_related().order_by('measured_at')
        
        if not records:
            return JsonResponse({
                'success': True,
                'data': {
                    'student_info': {
                        'id': student.id,
                        'name': get_korean_name(student.user),
                        'class': student.school_class.name,  
                        'grade': student.school_class.grade
                    },
                    'activity_info': {
                        'id': str(activity.id),
                        'name': get_activity_display_name(activity.name),
                        'unit': get_activity_unit(activity.name)
                    },
                    'growth_data': {
                        'records': [],
                        'statistics': {
                            'average_growth': 0,
                            'best_record': 0,
                            'worst_record': 0,
                            'total_measurements': 0
                        }
                    }
                }
            })
        
        # 성장 데이터 처리
        growth_records = []
        previous_value = None
        values = []
        
        for record in records:
            try:
                session = PAPSSession.objects.get(id=record.session_id)
                measurement_value = get_measurement_value(activity.name, record.measurement_data)
                
                # 성장률 계산
                growth_rate = None
                if previous_value is not None and previous_value != 0:
                    # 종목별 성장률 계산 방식
                    if activity.name in ['FIFTY_METER_RUN']:  # 시간 기록 (낮을수록 좋음)
                        growth_rate = (previous_value - measurement_value) / previous_value * 100
                    else:  # 일반 기록 (높을수록 좋음)
                        growth_rate = (measurement_value - previous_value) / previous_value * 100
                
                growth_records.append({
                    'session_name': session.name,
                    'date': record.measured_at.strftime('%Y-%m-%d') if record.measured_at else session.measurement_date.strftime('%Y-%m-%d'),
                    'value': measurement_value,
                    'grade': record.evaluation_grade,
                    'growth_rate': round(growth_rate, 1) if growth_rate is not None else None
                })
                
                values.append(measurement_value)
                previous_value = measurement_value
                
            except PAPSSession.DoesNotExist:
                continue
        
        # 통계 계산
        growth_rates = [r['growth_rate'] for r in growth_records if r['growth_rate'] is not None]
        statistics_data = {
            'average_growth': round(sum(growth_rates) / len(growth_rates), 1) if growth_rates else 0,
            'best_record': max(values) if values else 0,
            'worst_record': min(values) if values else 0,
            'total_measurements': len(growth_records)
        }
        
        # 시간 기록 종목의 경우 best/worst 반전
        if activity.name in ['FIFTY_METER_RUN']:
            statistics_data['best_record'], statistics_data['worst_record'] = statistics_data['worst_record'], statistics_data['best_record']
        
        return JsonResponse({
            'success': True,
            'data': {
                'student_info': {
                    'id': student.id,
                    'name': get_korean_name(student.user),
                    'class': student.school_class.name,
                    'grade': student.school_class.grade,
                    'grade_display': get_grade_display_name(student.school_class.grade)
                },
                'activity_info': {
                    'id': str(activity.id),
                    'name': get_activity_display_name(activity.name),
                    'unit': get_activity_unit(activity.name)
                },
                'growth_data': {
                    'records': growth_records,
                    'statistics': statistics_data
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 처리 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
def api_get_class_students(request):
    """개인별 통계용 학급 학생 목록 조회 API"""
    try:
        teacher = request.user.teacher
        class_id = request.GET.get('class_id')
        
        if not class_id:
            return JsonResponse({
                'success': False, 
                'error': '학급을 선택해주세요.'
            })
        
        # 학급 조회
        try:
            class_instance = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 학급을 찾을 수 없습니다.'
            })
        
        # 권한 확인 - 교사가 해당 학급을 담당하는지 확인
        if not ClassTeacher.objects.filter(
            teacher=teacher, 
            class_instance=class_instance
        ).exists():
            return JsonResponse({
                'success': False,
                'error': '해당 학급에 대한 권한이 없습니다.'
            })
        
        # 학생 목록 조회
        students = Student.objects.filter(
            school_class=class_instance
        ).select_related('user').order_by('student_id')
        
        # 응답 데이터 구성
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'name': get_korean_name(student.user),
                'student_number': student.student_id  # JavaScript와 일치
            })
        
        return JsonResponse({
            'success': True,
            'students': students_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
def class_compare_view(request):
    """학급 평균 비교 페이지 (SSR)"""
    teacher = request.user.teacher
    
    # 담당 학급 조회
    teacher_classes = ClassTeacher.objects.filter(
        teacher=teacher
    ).select_related('class_instance', 'class_instance__school')
    
    # 담당 학급 목록
    classes = []
    for tc in teacher_classes:
        classes.append({
            'id': tc.class_instance.id,
            'name': f"{tc.class_instance.grade}학년 {tc.class_instance.class_number}반",
            'grade': tc.class_instance.grade,
        })
    
    # 측정회차 목록
    sessions = PAPSSession.objects.filter(
        teacher_id=teacher.id,
        is_active=True
    ).order_by('-school_year', '-measurement_date')
    
    # 체력요인 목록 (필수평가 5개)
    categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.REQUIRED
    ).order_by('order')
    
    context = {
        'classes': classes,
        'sessions': sessions,
        'categories': categories,
    }
    
    return render(request, 'physical_education/teachers/statistics/class/compare.html', context)


@login_required
@teacher_required
def class_distribution_view(request):
    """체력요인별 분포 페이지 (SSR)"""
    teacher = request.user.teacher
    
    # 담당 학급 조회
    teacher_classes = ClassTeacher.objects.filter(
        teacher=teacher
    ).select_related('class_instance', 'class_instance__school')
    
    # 담당 학급 목록
    classes = []
    for tc in teacher_classes:
        classes.append({
            'id': tc.class_instance.id,
            'name': f"{tc.class_instance.grade}학년 {tc.class_instance.class_number}반",
            'grade': tc.class_instance.grade,
        })
    
    # 측정회차 목록
    sessions = PAPSSession.objects.filter(
        teacher_id=teacher.id,
        is_active=True
    ).order_by('-school_year', '-measurement_date')
    
    # 체력요인 목록 (필수평가 5개)
    categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.REQUIRED
    ).order_by('order')
    
    context = {
        'classes': classes,
        'sessions': sessions,
        'categories': categories,
    }
    
    return render(request, 'physical_education/teachers/statistics/class/distribution.html', context)


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_class_compare(request):
    """학급 평균 비교 데이터 API"""
    try:
        teacher = request.user.teacher
        session_id = request.GET.get('session_id')
        category_id = request.GET.get('category_id')
        class_ids = request.GET.getlist('class_ids')
        
        if not all([session_id, category_id]):
            return JsonResponse({
                'success': False,
                'error': '측정회차와 체력요인을 모두 선택해주세요.'
            })
        
        # 세션 권한 확인
        try:
            session = PAPSSession.objects.get(id=session_id, teacher_id=teacher.id)
        except PAPSSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '측정회차를 찾을 수 없습니다.'
            })
        
        # 체력요인 정보 조회
        try:
            category = PAPSCategory.objects.get(id=category_id)
        except PAPSCategory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '체력요인을 찾을 수 없습니다.'
            })
        
        # 담당 학급들 조회 (class_ids가 없으면 모든 담당 학급)
        if class_ids:
            # 선택된 학급들 권한 확인
            valid_classes = []
            for class_id in class_ids:
                try:
                    class_instance = Class.objects.get(id=class_id)
                    if ClassTeacher.objects.filter(teacher=teacher, class_instance=class_instance).exists():
                        valid_classes.append(class_instance)
                except Class.DoesNotExist:
                    continue
        else:
            # 모든 담당 학급 조회
            teacher_classes = ClassTeacher.objects.filter(
                teacher=teacher
            ).select_related('class_instance')
            valid_classes = [tc.class_instance for tc in teacher_classes]
        
        if not valid_classes:
            return JsonResponse({
                'success': False,
                'error': '담당하고 계신 학급이 없습니다.'
            })
        
        # 각 학급별 체력요인 평균 계산
        class_data = []
        
        for class_instance in valid_classes:
            # 해당 학급 학생들 조회
            students = Student.objects.filter(school_class=class_instance).values_list('id', flat=True)
            
            # 해당 체력요인의 활동들 조회
            activities = PAPSActivity.objects.filter(category_id=category_id)
            
            # 학급 평균 계산
            total_grades = []
            activity_averages = []
            
            for activity in activities:
                # 해당 활동이 활성화되어 있는지 확인
                is_activity_active = PAPSSessionActivity.objects.filter(
                    session_id=session_id,
                    activity_id=activity.id,
                    is_active=True
                ).exists()
                
                if not is_activity_active:
                    continue
                
                # 해당 활동의 측정 기록 조회 (활성 종목만)
                records = PAPSRecord.objects.filter(
                    session_id=session_id,
                    activity_id=activity.id,
                    student_id__in=students,
                    evaluation_grade__isnull=False
                ).values_list('evaluation_grade', flat=True)
                
                if records:
                    activity_avg = sum(records) / len(records)
                    activity_averages.append({
                        'activity': get_activity_display_name(activity.name),
                        'average': round(activity_avg, 2),
                        'count': len(records)
                    })
                    total_grades.extend(records)
            
            # 학급 전체 평균
            class_average = round(sum(total_grades) / len(total_grades), 2) if total_grades else 0
            
            class_data.append({
                'class_id': class_instance.id,
                'class_name': f"{class_instance.grade}학년 {class_instance.class_number}반",
                'grade': class_instance.grade,
                'average': class_average,
                'student_count': len(students),
                'measured_count': len(total_grades),
                'activities': activity_averages
            })
        
        # 차트 데이터 구성
        chart_data = {
            'labels': [cd['class_name'] for cd in class_data],
            'averages': [cd['average'] for cd in class_data],
            'counts': [cd['measured_count'] for cd in class_data]
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'session_info': {
                    'id': str(session.id),
                    'name': session.name,
                    'date': session.measurement_date.strftime('%Y-%m-%d')
                },
                'category_info': {
                    'id': str(category.id),
                    'name': category.get_name_display()
                },
                'class_data': class_data,
                'chart_data': chart_data,
                'statistics': {
                    'total_classes': len(class_data),
                    'highest_average': max([cd['average'] for cd in class_data]) if class_data else 0,
                    'lowest_average': min([cd['average'] for cd in class_data]) if class_data else 0,
                    'overall_average': round(sum([cd['average'] for cd in class_data]) / len(class_data), 2) if class_data else 0
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 처리 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
@require_http_methods(["GET"])
def api_class_distribution(request):
    """체력요인별 분포 데이터 API"""
    try:
        teacher = request.user.teacher
        session_id = request.GET.get('session_id')
        category_id = request.GET.get('category_id')
        class_id = request.GET.get('class_id')
        
        if not all([session_id, category_id, class_id]):
            return JsonResponse({
                'success': False,
                'error': '측정회차, 체력요인, 학급을 모두 선택해주세요.'
            })
        
        # 세션 권한 확인
        try:
            session = PAPSSession.objects.get(id=session_id, teacher_id=teacher.id)
        except PAPSSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '측정회차를 찾을 수 없습니다.'
            })
        
        # 체력요인 정보 조회
        try:
            category = PAPSCategory.objects.get(id=category_id)
        except PAPSCategory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '체력요인을 찾을 수 없습니다.'
            })
        
        # 학급 권한 확인
        try:
            class_instance = Class.objects.get(id=class_id)
            if not ClassTeacher.objects.filter(teacher=teacher, class_instance=class_instance).exists():
                return JsonResponse({
                    'success': False,
                    'error': '해당 학급에 대한 권한이 없습니다.'
                })
        except Class.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '학급을 찾을 수 없습니다.'
            })
        
        # 해당 학급 학생들 조회
        students = Student.objects.filter(school_class=class_instance)
        total_students = students.count()
        student_ids = students.values_list('id', flat=True)
        
        # 해당 체력요인의 활동들 조회
        activities = PAPSActivity.objects.filter(category_id=category_id)
        
        # 등급별 분포 계산
        grade_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        measured_students = set()
        activity_distributions = []
        all_values = []
        
        for activity in activities:
            # 해당 활동이 활성화되어 있는지 확인
            is_activity_active = PAPSSessionActivity.objects.filter(
                session_id=session_id,
                activity_id=activity.id,
                is_active=True
            ).exists()
            
            if not is_activity_active:
                continue
            
            # 해당 활동의 측정 기록 조회 (활성 종목만)
            records = PAPSRecord.objects.filter(
                session_id=session_id,
                activity_id=activity.id,
                student_id__in=student_ids,
                evaluation_grade__isnull=False
            )
            
            activity_grades = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            values = []
            
            for record in records:
                grade = record.evaluation_grade
                grade_distribution[grade] += 1
                activity_grades[grade] += 1
                measured_students.add(record.student_id)
                
                # 측정값 추출
                measurement_value = get_measurement_value(activity.name, record.measurement_data)
                if measurement_value is not None:
                    values.append(measurement_value)
                    all_values.append(measurement_value)
            
            if values:
                import statistics
                activity_distributions.append({
                    'activity': get_activity_display_name(activity.name),
                    'unit': get_activity_unit(activity.name),
                    'count': len(values),
                    'average': round(statistics.mean(values), 2),
                    'min': min(values),
                    'max': max(values),
                    'grade_distribution': activity_grades,
                    'values': values  # 박스플롯용
                })
        
        # 전체 통계 계산
        measured_count = len(measured_students)
        unmeasured_count = total_students - measured_count
        
        # 파이 차트 데이터
        pie_data = {
            'labels': ['1등급', '2등급', '3등급', '4등급', '5등급', '미측정'],
            'data': [
                grade_distribution[1],
                grade_distribution[2], 
                grade_distribution[3],
                grade_distribution[4],
                grade_distribution[5],
                unmeasured_count
            ],
            'colors': [
                '#3B82F6',  # 파란색
                '#10B981',  # 초록색
                '#F59E0B',  # 노란색
                '#F97316',  # 주황색
                '#EF4444',  # 빨간색
                '#9CA3AF'   # 회색
            ]
        }
        
        # 박스플롯 데이터 (전체 측정값)
        boxplot_data = None
        if all_values:
            import statistics
            all_values.sort()
            n = len(all_values)
            boxplot_data = {
                'min': min(all_values),
                'q1': all_values[n//4] if n >= 4 else min(all_values),
                'median': statistics.median(all_values),
                'q3': all_values[3*n//4] if n >= 4 else max(all_values),
                'max': max(all_values),
                'outliers': []  # 간단히 하기 위해 이상치는 제외
            }
        
        return JsonResponse({
            'success': True,
            'data': {
                'session_info': {
                    'id': str(session.id),
                    'name': session.name,
                    'date': session.measurement_date.strftime('%Y-%m-%d')
                },
                'category_info': {
                    'id': str(category.id),
                    'name': category.get_name_display()
                },
                'class_info': {
                    'id': class_instance.id,
                    'name': f"{class_instance.grade}학년 {class_instance.class_number}반",
                    'total_students': total_students,
                    'measured_students': measured_count,
                    'unmeasured_students': unmeasured_count
                },
                'distribution': {
                    'pie_data': pie_data,
                    'boxplot_data': boxplot_data,
                    'activity_distributions': activity_distributions,
                    'grade_distribution': grade_distribution
                },
                'statistics': {
                    'completion_rate': round(measured_count / total_students * 100, 1),
                    'average_grade': round(sum([g*c for g, c in grade_distribution.items()]) / sum(grade_distribution.values()), 2) if sum(grade_distribution.values()) > 0 else 0,
                    'most_common_grade': max(grade_distribution, key=grade_distribution.get)
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'데이터 처리 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@teacher_required
def paps_batch_measurement_view(request):
    """PAPS 일괄입력 뷰"""
    teacher_id = request.user.teacher.id

    # 전체 카테고리 조회 (필수평가 + 선택평가)
    all_categories = PAPSCategory.objects.all().order_by("order")

    # 전체 활동(종목) 조회
    all_activities = PAPSActivity.objects.all()

    # 교사의 측정회차 목록 조회
    available_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).order_by(
        "-created_at"
    )

    # 교사가 담당하는 학급들 조회 (ClassTeacher 모델 기반)
    teacher_classes = (
        ClassTeacher.objects.filter(teacher_id=teacher_id)
        .select_related("class_instance")
        .order_by("class_instance__grade", "class_instance__class_number")
    )

    # 교사가 담당하는 실제 학년 목록 추출 (중복 제거, PAPS 대상만)
    paps_grades = set()
    for ct in teacher_classes:
        grade = ct.class_instance.grade
        if 4 <= grade <= 12:  # PAPS 대상: 초4~고3
            paps_grades.add(grade)

    # 학년 선택지 생성 (실제 담당 학년만)
    grade_choices = [
        (grade, get_grade_display_name(grade)) for grade in sorted(paps_grades)
    ]

    # 교사가 담당하는 실제 학급 목록 생성
    available_classes = []
    for ct in teacher_classes:
        cls = ct.class_instance
        if 4 <= cls.grade <= 12:  # PAPS 대상만
            available_classes.append(
                {
                    "id": cls.id,
                    "name": f"{cls.class_number}반",
                    "full_name": f"{cls.grade}학년 {cls.class_number}반",
                    "grade": cls.grade,
                    "class_number": cls.class_number,
                    "role": ct.get_role_display(),
                }
            )

    # 년도 범위 생성 (현재 년도 기준 ±5년)
    current_year = timezone.now().year
    year_range = range(current_year - 5, current_year + 6)

    # 전체 카테고리 JSON 직렬화를 위한 처리
    all_categories_json = []
    for category in all_categories:
        all_categories_json.append(
            {
                "id": str(category.id),
                "name": category.name,
                "display_name": category.get_name_display(),
                "evaluation_type": category.evaluation_type,
                "order": category.order,
            }
        )

    # 전체 활동(종목) JSON 직렬화를 위한 처리
    all_activities_json = []
    for activity in all_activities:
        all_activities_json.append(
            {
                "id": str(activity.id),
                "name": activity.name,
                "display_name": activity.get_name_display(),
                "category_id": str(activity.category_id),
                "measurement_schema": activity.measurement_schema,
                "evaluation_criteria": activity.evaluation_criteria,
            }
        )

    # 측정회차 JSON 직렬화를 위한 처리
    sessions_json = []
    for session in available_sessions:
        sessions_json.append(
            {
                "id": str(session.id),
                "name": session.name,
                "school_year": session.school_year,
                "session_type": session.session_type,
                "session_type_display": session.get_session_type_display(),
                "measurement_date": session.measurement_date.strftime("%Y-%m-%d"),
                "is_completed": session.is_completed,
            }
        )

    context = {
        "all_categories": all_categories,
        "all_activities": all_activities,
        "available_sessions": available_sessions,
        "available_classes": available_classes,
        "grade_choices": grade_choices,
        "year_range": year_range,
        "current_year": current_year,
        "evaluation_type": "batch",
        "title": "PAPS 일괄입력",
        # JavaScript에서 사용할 JSON 데이터
        "all_categories_json": json.dumps(all_categories_json),
        "all_activities_json": json.dumps(all_activities_json),
        "available_sessions_json": json.dumps(sessions_json),
        "available_classes_json": json.dumps(available_classes),
        "grade_choices_json": json.dumps(grade_choices),
    }
    return render(
        request, "physical_education/teachers/paps/measurement/batch_input.html", context
    )


@login_required
@teacher_required
def paps_measure_view(request):
    """PAPS 측정하기 뷰"""
    teacher_id = request.user.teacher.id
    
    # 1. 측정회차 데이터
    sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id
    ).order_by("-school_year", "-measurement_date")
    
    # 2. 활성화된 PAPSSessionActivity 전체 데이터 조회
    session_ids = sessions.values_list('id', flat=True)
    active_session_activities = PAPSSessionActivity.objects.filter(
        session_id__in=session_ids,
        is_active=True
    ).order_by('session_id', 'grade', 'category_id')
    
    # PAPSSessionActivity 데이터 구조화
    session_activities_data = []
    for activity in active_session_activities:
        session_activities_data.append({
            'id': str(activity.id),
            'session_id': str(activity.session_id),
            'grade': activity.grade,
            'grade_display': activity.get_grade_display(),
            'category_id': str(activity.category_id),
            'activity_id': str(activity.activity_id),
            'is_active': activity.is_active,
            'created_at': activity.created_at.isoformat() if activity.created_at else None
        })
    
    # 학년 정보 추출 (기존 로직 유지)
    active_grades = set(sa['grade'] for sa in session_activities_data)
    
    # 3. 담당 학급 데이터 (활성화된 학년만)
    teacher_classes = ClassTeacher.objects.filter(
        teacher_id=teacher_id
    ).select_related("class_instance").order_by(
        "class_instance__grade", 
        "class_instance__class_number"
    )
    
    # 활성화된 학년에 해당하는 학급만 필터링
    classes_data = []
    grades_set = set()
    for ct in teacher_classes:
        cls = ct.class_instance
        if cls.grade in active_grades:
            classes_data.append({
                "id": cls.id,
                "grade": cls.grade,
                "class_number": cls.class_number,
                "name": f"{cls.grade}학년 {cls.class_number}반"
            })
            grades_set.add(cls.grade)
    
    # 학년도 목록
    school_years = sorted(set(
        sessions.values_list("school_year", flat=True)
    ), reverse=True)
    
    # 3. PAPS 카테고리 데이터를 배열로 처리
    categories = PAPSCategory.objects.all().order_by("order")
    categories_data = []
    for category in categories:
        categories_data.append({
            "id": str(category.id),
            "name": category.name,  # 원본 (예: "CARDIO")
            "display_name": category.get_name_display(),  # 한글명 (예: "심폐지구력")
            "evaluation_type": category.evaluation_type,
            "order": category.order
        })
    
    # 4. PAPS 활동 데이터를 배열로 처리
    activities = PAPSActivity.objects.all().order_by("created_at")
    activities_data = []
    for activity in activities:
        activities_data.append({
            "id": str(activity.id),
            "name": activity.name,  # 원본 (예: "SHUTTLE_RUN")
            "display_name": activity.get_name_display(),  # 한글명 (예: "왕복오래달리기")
            "category_id": str(activity.category_id),
            "measurement_schema": activity.measurement_schema,
            "evaluation_criteria": activity.evaluation_criteria,
            "created_at": activity.created_at.isoformat() if activity.created_at else None
        })
    
    # 세션 데이터를 JSON 직렬화 가능한 형태로 변환
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            "id": str(session.id),
            "name": session.name,
            "teacher_id": session.teacher_id,
            "school_year": session.school_year,
            "session_type": session.session_type,
            "session_type_display": session.get_session_type_display(),
            "measurement_date": session.measurement_date.isoformat() if session.measurement_date else None,
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat() if session.created_at else None
        })
    
    context = {
        "school_years": school_years,
        # JSON 직렬화된 데이터 추가
        "classes_json": json.dumps(classes_data),
        "sessions_json": json.dumps(sessions_data),
        "categories_json": json.dumps(categories_data),
        "activities_json": json.dumps(activities_data),
        "session_activities_json": json.dumps(session_activities_data),
    }

    return render(request, "physical_education/teachers/paps/measurement/measure.html", context)