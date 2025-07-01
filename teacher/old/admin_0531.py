# teacher/admin.py
from django.contrib import admin
from ..models import Course, Chapter, CourseAssignment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'target', 'teacher', 'created_at', 'updated_at']
    list_filter = ['teacher__school', 'created_at', 'updated_at']
    search_fields = ['subject_name', 'target', 'description']
    raw_id_fields = ['teacher']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 교사는 자신의 코스만 볼 수 있음
        if hasattr(request.user, 'teacher'):
            return qs.filter(teacher=request.user.teacher)
        return qs.none()

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['chapter_title', 'subject', 'chapter_order']
    list_filter = ['subject__teacher__school', 'subject']
    search_fields = ['chapter_title', 'subject__subject_name']
    ordering = ['subject', 'chapter_order']

@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['course', 'get_assigned_to', 'assigned_date', 'due_date']
    list_filter = ['assigned_date', 'due_date']
    search_fields = ['course__subject_name']
    raw_id_fields = ['course', 'assigned_class', 'assigned_student']
    
    def get_assigned_to(self, obj):
        if obj.assigned_class:
            return f"학급: {obj.assigned_class.name}"
        elif obj.assigned_student:
            return f"학생: {obj.assigned_student.user.get_full_name()}"
        return "미할당"
    get_assigned_to.short_description = '할당 대상'
