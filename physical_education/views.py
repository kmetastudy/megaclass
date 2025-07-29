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
from .utils import calculate_paps_grade
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
    name = student.user.get_full_name() or student.user.username

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

    # 통계 데이터 계산
    total_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).count()

    # 진행 중인 측정회차 (완료되지 않은 회차)
    active_sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id, is_completed=False
    ).count()

    # 이번 달 측정회차
    from datetime import datetime

    current_month = datetime.now().month
    current_year = datetime.now().year

    this_month_sessions = PAPSSession.objects.filter(
        teacher_id=teacher_id,
        measurement_date__month=current_month,
        measurement_date__year=current_year,
    ).count()

    # 총 측정 기록 수 (참여 학생 수로 사용)
    total_records = PAPSRecord.objects.filter(measured_by_teacher_id=teacher_id).count()

    # 최근 측정회차 5개
    recent_sessions = PAPSSession.objects.filter(teacher_id=teacher_id).order_by(
        "-created_at"
    )[:5]

    # 각 측정회차별 진행률 계산
    session_progress = []
    for session in recent_sessions:
        # 해당 회차의 총 활동 수 (활성 상태인 것만)
        total_activities = PAPSSessionActivity.objects.filter(
            session_id=session.id,
            is_active=True
        ).count()

        # 측정 완료된 기록 수 (활성 종목에 대한 기록만)
        completed_records = PAPSRecord.objects.active_for_session(session.id).count()

        # 진행률 계산 (임시로 간단한 계산)
        progress_percentage = (
            min(100, (completed_records * 10)) if total_activities > 0 else 0
        )

        session_progress.append(
            {
                "session": session,
                "progress": progress_percentage,
                "total_activities": total_activities,
                "completed_records": completed_records,
            }
        )

    context = {
        "user": request.user,
        "stats": {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "this_month_sessions": this_month_sessions,
            "total_records": total_records,
        },
        "recent_sessions": session_progress,
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
    # 선택평가 카테고리 조회
    optional_categories = PAPSCategory.objects.filter(
        evaluation_type=PAPSCategory.OPTIONAL
    ).order_by("order")

    context = {
        "categories": optional_categories,
        "evaluation_type": "optional",
        "title": "PAPS 선택평가 입력",
    }
    return render(request, "physical_education/paps/measurement/input.html", context)


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

        # 측정 데이터 업데이트
        record.measurement_data = measurement_data
        record.measured_at = timezone.now()
        record.save()

        return JsonResponse(
            {"success": True, "record_id": str(record.id), "updated": True}
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "JSON 데이터가 올바르지 않습니다."}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def api_paps_calculate_grade(request):
    """PAPS 등급 계산 API"""
    try:
        if request.method == "GET":
            data = request.GET
        else:
            data = json.loads(request.body)

        activity_id = data.get("activity_id")
        measurement_data = data.get("measurement_data", {})
        student_grade = int(data.get("student_grade", 6))

        if not activity_id:
            return JsonResponse(
                {"success": False, "error": "activity_id가 필요합니다."}
            )

        activity = get_object_or_404(PAPSActivity, id=activity_id)

        # 등급 계산
        grade_result = calculate_paps_grade(
            activity=activity,
            measurement_data=measurement_data,
            student_grade=student_grade,
        )

        return JsonResponse({"success": True, "grade_result": grade_result})

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
                    "name": activity.get_name_display(),
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
                    "name": student.user.get_full_name() or student.user.username,
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
