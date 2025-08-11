from django.urls import path
from . import views, apis, measurement_views, emails

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
    path(
        "teachers/paps/measurement/batch/",
        views.paps_batch_measurement_view,
        name="paps_batch_measurement",
    ),
    path(
        "teachers/paps/measurement/measure/",
        views.paps_measure_view,
        name="paps_measure",
    ),
    # PAPS 측정 화면 동적 로드 (HTMX용)
    path(
        "paps/load-measurement/",
        measurement_views.paps_load_measurement_view,
        name="paps_load_measurement",
    ),
    # PAPS API 엔드포인트
    path(
        "api/paps/save-measurement/",
        views.api_paps_save_measurement,
        name="api_paps_save_measurement",
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
    # 특정 활동에 대한 측정 기록 조회 API
    path(
        "api/paps/measurements/by-activity/",
        views.api_paps_get_measurements_by_activity,
        name="api_paps_get_measurements_by_activity",
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
    # 세션별 활성 활동 조회 (일괄입력용)
    path(
        "api/paps/session-activities/",
        apis.api_get_session_activities,
        name="api_get_session_activities",
    ),
    # 일괄입력 API
    path(
        "api/paps/get-batch-records/",
        apis.api_get_batch_records,
        name="api_get_batch_records",
    ),
    path(
        "api/paps/batch-save-measurements/",
        apis.api_batch_save_measurements,
        name="api_batch_save_measurements",
    ),
    # 엑셀 Export API
    path(
        "api/paps/export-records/",
        apis.api_export_paps_records,
        name="api_export_paps_records",
    ),
    path(
        "api/paps/download-template/",
        apis.api_download_paps_template,
        name="api_download_paps_template",
    ),
    
    # PAPS 통계 페이지
    # 개인별 통계
    path(
        "teachers/statistics/individual/profile/",
        views.individual_profile_view,
        name="individual_profile",
    ),
    path(
        "teachers/statistics/individual/growth/",
        views.individual_growth_view,
        name="individual_growth",
    ),
    # 학급별 통계
    path(
        "teachers/statistics/class/compare/",
        views.class_compare_view,
        name="class_compare",
    ),
    path(
        "teachers/statistics/class/distribution/",
        views.class_distribution_view,
        name="class_distribution",
    ),
    # 종목별 분석
    path(
        "teachers/statistics/activity/average/",
        views.activity_average_view,
        name="activity_average",
    ),
    path(
        "teachers/statistics/activity/grade-distribution/",
        views.grade_distribution_view,
        name="grade_distribution",
    ),
    
    # PAPS 통계 API
    # 개인별 통계용 학생 목록 API
    path(
        "api/paps/class-students/",
        views.api_get_class_students,
        name="api_get_class_students",
    ),
    # 개인별 통계 API
    path(
        "api/paps/statistics/individual-profile/",
        views.api_individual_profile,
        name="api_individual_profile",
    ),
    path(
        "api/paps/statistics/individual-growth/",
        views.api_individual_growth,
        name="api_individual_growth",
    ),
    # 학급별 통계 API
    path(
        "api/paps/statistics/class-compare/",
        views.api_class_compare,
        name="api_class_compare",
    ),
    path(
        "api/paps/statistics/class-distribution/",
        views.api_class_distribution,
        name="api_class_distribution",
    ),
    # 종목별 분석 API
    path(
        "api/paps/statistics/activity-average/",
        views.api_activity_average,
        name="api_activity_average",
    ),
    path(
        "api/paps/statistics/grade-distribution/",
        views.api_grade_distribution,
        name="api_grade_distribution",
    ),
    
    # 이메일 전송 API
    path(
        "api/send-inquiry/",
        emails.api_send_inquiry,
        name="api_send_inquiry",
    ),
]
