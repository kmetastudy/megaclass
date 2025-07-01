from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import *

@admin.register(NCSCompetency)
class NCSCompetencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'competency_name', 'main_category', 'sub_category', 'level', 'order', 'is_active']
    list_filter = ['level', 'main_category', 'sub_category', 'is_active']
    search_fields = ['code', 'competency_name', 'main_category', 'sub_category']
    ordering = ['level', 'order', 'code']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('code', 'competency_name', 'description')
        }),
        ('분류', {
            'fields': ('main_category', 'sub_category', 'level', 'parent')
        }),
        ('설정', {
            'fields': ('order', 'is_active')
        }),
    )

@admin.register(NCSLearningSession)
class NCSLearningSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'student_name', 'session_type', 'total_questions', 'completed_questions', 
                    'correct_answers', 'score', 'is_completed', 'started_at', 'view_questions']
    list_filter = ['session_type', 'is_completed', 'started_at']
    search_fields = ['id', 'student__user__first_name', 'student__user__last_name', 'student__user__username']
    date_hierarchy = 'started_at'
    readonly_fields = ['score', 'started_at', 'completed_at']
    filter_horizontal = ['competencies']
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = '학생'
    
    def view_questions(self, obj):
        count = obj.questions.count()
        url = reverse("admin:ncs_ncsquestion_changelist") + f"?session__id__exact={obj.id}"
        return format_html('<a href="{}">문제 {}개 보기</a>', url, count)
    view_questions.short_description = '문제'
    
    actions = ['mark_completed', 'delete_incomplete_sessions']
    
    def mark_completed(self, request, queryset):
        queryset.update(is_completed=True, completed_at=timezone.now())
    mark_completed.short_description = "선택한 세션을 완료 처리"
    
    def delete_incomplete_sessions(self, request, queryset):
        deleted = queryset.filter(is_completed=False).delete()
        self.message_user(request, f"{deleted[0]}개의 미완료 세션이 삭제되었습니다.")
    delete_incomplete_sessions.short_description = "미완료 세션 삭제"

@admin.register(NCSQuestion)
class NCSQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'student_name', 'competency', 'order', 'is_answered', 
                    'student_answer', 'is_correct', 'time_spent', 'current_attempt_count']
    list_filter = ['is_answered', 'is_correct', 'session__session_type', 'competency__main_category']
    search_fields = ['session__student__user__first_name', 'session__student__user__last_name', 
                     'competency__competency_name']
    raw_id_fields = ['session', 'content']
    
    def session_id(self, obj):
        return obj.session.id
    session_id.short_description = '세션 ID'
    
    def student_name(self, obj):
        return obj.session.student.user.get_full_name()
    student_name.short_description = '학생'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__student__user', 'competency')

@admin.register(NCSStudentAnswer)
class NCSStudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'question_order', 'student_name', 'answer', 
                    'is_correct', 'attempt_count', 'time_spent', 'submitted_at']
    list_filter = ['is_correct', 'attempt_count', 'submitted_at']
    search_fields = ['student__username', 'student__first_name', 'student__last_name', 
                     'session__id', 'question__id']
    date_hierarchy = 'submitted_at'
    raw_id_fields = ['session', 'question', 'student']
    
    def session_id(self, obj):
        return obj.session.id
    session_id.short_description = '세션 ID'
    
    def question_order(self, obj):
        return obj.question.order
    question_order.short_description = '문제 번호'
    
    def student_name(self, obj):
        return obj.student.get_full_name()
    student_name.short_description = '학생'

@admin.register(NCSQuestionAttempt)
class NCSQuestionAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'question_id', 'student_name', 'attempt_number', 'answer', 
                    'is_correct', 'time_spent', 'attempted_at']
    list_filter = ['is_correct', 'attempt_number', 'attempted_at']
    search_fields = ['student__user__first_name', 'student__user__last_name', 
                     'question__id', 'question__session__id']
    date_hierarchy = 'attempted_at'
    raw_id_fields = ['question', 'student']
    
    def question_id(self, obj):
        return obj.question.id
    question_id.short_description = '문제 ID'
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = '학생'

@admin.register(NCSCompetencyAnalysis)
class NCSCompetencyAnalysisAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'competency', 'accuracy_rate', 'total_attempts', 
                    'correct_count', 'incorrect_count', 'weakness_score', 'updated_at']
    list_filter = ['competency__main_category', 'competency__sub_category', 'updated_at']
    search_fields = ['student__user__first_name', 'student__user__last_name', 
                     'competency__competency_name']
    ordering = ['-weakness_score']
    readonly_fields = ['accuracy_rate', 'weakness_score', 'updated_at']
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = '학생'
    
    actions = ['recalculate_analysis']
    
    def recalculate_analysis(self, request, queryset):
        for analysis in queryset:
            analysis.update_analysis()
        self.message_user(request, f"{queryset.count()}개의 분석이 재계산되었습니다.")
    recalculate_analysis.short_description = "분석 데이터 재계산"

@admin.register(NCSAssignment)
class NCSAssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'assignment_type', 'teacher', 'assigned_class', 
                    'question_count', 'due_date', 'is_active', 'created_at']
    list_filter = ['assignment_type', 'is_active', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'teacher__user__first_name', 
                     'teacher__user__last_name', 'assigned_class__name']
    filter_horizontal = ['assigned_students', 'competencies']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'description', 'assignment_type', 'teacher')
        }),
        ('할당 대상', {
            'fields': ('assigned_class', 'assigned_students')
        }),
        ('문제 설정', {
            'fields': ('competencies', 'question_count')
        }),
        ('일정', {
            'fields': ('due_date', 'is_active')
        }),
    )

@admin.register(NCSClassStatistics)
class NCSClassStatisticsAdmin(admin.ModelAdmin):
    list_display = ['class_obj', 'competency', 'average_accuracy', 'total_students', 
                    'participated_students', 'average_attempts', 'updated_at']
    list_filter = ['class_obj', 'competency__main_category', 'updated_at']
    search_fields = ['class_obj__name', 'competency__competency_name']
    date_hierarchy = 'updated_at'
    readonly_fields = ['updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('class_obj', 'competency')

# Admin 사이트 커스터마이징
admin.site.site_header = "NCS 학습 관리 시스템"
admin.site.site_title = "NCS Admin"
admin.site.index_title = "NCS 학습 관리"