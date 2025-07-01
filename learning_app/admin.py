from django.contrib import admin
from .models import *

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'employee_id', 'created_at']
    list_filter = ['school']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['school', 'grade', 'class_number', 'teacher', 'created_at']
    list_filter = ['school', 'grade']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'school_class', 'student_id', 'created_at']
    list_filter = ['school_class']
    search_fields = ['user__first_name', 'user__last_name', 'student_id']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'target', 'teacher', 'created_at']
    list_filter = ['teacher', 'created_at']
    search_fields = ['subject_name', 'target']

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['subject', 'chapter_title', 'chapter_order']
    list_filter = ['subject']
    ordering = ['subject', 'chapter_order']

@admin.register(SubChapter)
class SubChapterAdmin(admin.ModelAdmin):
    list_display = ['chapter', 'sub_chapter_title', 'sub_chapter_order']
    list_filter = ['chapter__subject']
    ordering = ['chapter', 'sub_chapter_order']

@admin.register(Chasi)
class ChasiAdmin(admin.ModelAdmin):
    list_display = ['sub_chapter', 'chasi_title', 'chasi_order']
    list_filter = ['subject']
    ordering = ['sub_chapter', 'chasi_order']

@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ['type_name', 'description']

@admin.register(Contents)
class ContentsAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['title']

@admin.register(ChasiSlide)
class ChasiSlideAdmin(admin.ModelAdmin):
    list_display = ['chasi', 'slide_number', 'content_type']
    list_filter = ['chasi__subject', 'content_type']
    ordering = ['chasi', 'slide_number']

@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['course', 'assigned_class', 'assigned_student', 'assigned_date']
    list_filter = ['course', 'assigned_date']

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'chasi', 'slide', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'chasi__subject']

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['student', 'slide', 'is_correct', 'score', 'submitted_at']
    list_filter = ['is_correct', 'slide__chasi__subject']

@admin.register(StudentRecord)
class StudentRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'slide', 'session_number', 'recorded_at']
    list_filter = ['slide__chasi__subject', 'recorded_at']