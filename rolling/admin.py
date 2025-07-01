from django.contrib import admin
from .models import RollingAttempt, FeedbackCategory, RollingEvaluation

@admin.register(RollingAttempt)
class RollingAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'attempt_number', 'is_success', 'created_at']
    list_filter = ['is_success', 'created_at', 'student__school_class']
    search_fields = ['student__user__username', 'student__user__first_name', 'student__user__last_name']
    ordering = ['-created_at']

@admin.register(FeedbackCategory)
class FeedbackCategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'is_success_category']
    list_filter = ['is_success_category']

@admin.register(RollingEvaluation)
class RollingEvaluationAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher', 'grade', 'evaluated_at']
    list_filter = ['grade', 'evaluated_at']
    search_fields = ['student__user__username', 'teacher__user__username']