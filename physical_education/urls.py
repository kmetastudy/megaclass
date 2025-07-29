from django.urls import path
from . import views, apis

app_name = "physical_education"

urlpatterns = [
    # 체육 교사 대시보드
    path("teachers/", views.teacher_dashboard, name="teacher_dashboard"),
    # PAPS 측정회차 관리 (목록/생성/삭제 통합)
    path(
        "teachers/paps/sessions/",
        views.paps_session_list_view,
        name="paps_session_list",
    ),
    # PAPS 측정종목 선택 (PAPSSessionActivity 관리) - session_id 제거
    path(
        "teachers/paps/session-activities/",
        views.paps_session_activities_view,
        name="paps_session_activities",
    ),
    # PAPS 측정 입력 (직접 접근)
    path(
        "teachers/paps/measurement/required/",
        views.paps_required_measurement_view,
        name="paps_required_measurement",
    ),
    path(
        "teachers/paps/measurement/optional/",
        views.paps_optional_measurement_view,
        name="paps_optional_measurement",
    ),
    # PAPS API 엔드포인트
    path(
        "api/paps/save-measurement/",
        views.api_paps_save_measurement,
        name="api_paps_save_measurement",
    ),
    path(
        "api/paps/calculate-grade/",
        views.api_paps_calculate_grade,
        name="api_paps_calculate_grade",
    ),
    path(
        "api/paps/activities/<str:category>/",
        views.api_paps_get_activities,
        name="api_paps_get_activities",
    ),
    # 학생 목록 조회 API
    path(
        "api/students/by-class/",
        views.api_get_students_by_class,
        name="api_get_students_by_class",
    ),
    # PAPSSessionActivity 관리 API
    path(
        "api/paps/session-activities/form-fields/",
        apis.api_get_activity_form_fields,
        name="api_get_activity_form_fields",
    ),
    path(
        "api/paps/session-activities/save/",
        apis.api_save_session_activities,
        name="api_save_session_activities",
    ),
    path(
        "api/paps/session-activities/existing/",
        apis.api_get_existing_activities,
        name="api_get_existing_activities",
    ),
]
