# student/admin.py
from django.contrib import admin
from .models import StudentProgress, StudentAnswer,StudentPhysicalResult,PhysicalResultType


admin.site.register(PhysicalResultType)

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'slide', 'is_completed', 'started_at', 'completed_at']
    list_filter = ['is_completed', 'started_at', 'completed_at']
    search_fields = ['student__user__username', 'slide__chasi__chasi_title']
    raw_id_fields = ['student', 'slide']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 교사는 자신의 학생들만, 학생은 자신의 것만
        if hasattr(request.user, 'teacher'):
            return qs.filter(student__school_class__teacher=request.user.teacher)
        elif hasattr(request.user, 'student'):
            return qs.filter(student=request.user.student)
        return qs.none()

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['student', 'slide', 'is_correct', 'score', 'submitted_at']
    list_filter = ['is_correct', 'submitted_at']
    search_fields = ['student__user__username', 'slide__chasi__chasi_title']
    raw_id_fields = ['student', 'slide']
    readonly_fields = ['submitted_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 교사는 자신의 학생들만, 학생은 자신의 것만
        if hasattr(request.user, 'teacher'):
            return qs.filter(student__school_class__teacher=request.user.teacher)
        elif hasattr(request.user, 'student'):
            return qs.filter(student=request.user.student)
        return qs.none()
    
@admin.register(StudentPhysicalResult)
class StudentPhysicalResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'slide', 'record', 'score', 'submitted_at','writer']
    list_filter = [ 'submitted_at']
    search_fields = ['student__user__username', 'slide__chasi__chasi_title']
    raw_id_fields = ['student']
    readonly_fields = ['submitted_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 교사는 자신의 학생들만, 학생은 자신의 것만
        if hasattr(request.user, 'teacher'):
            return qs.filter(student__school_class__teacher=request.user.teacher)
        elif hasattr(request.user, 'student'):
            return qs.filter(student=request.user.student)
        return qs.none()
