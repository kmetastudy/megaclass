# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import School, Teacher, Class, Student,ClassTeacher

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'created_at']
    search_fields = ['name', 'address']
    list_filter = ['created_at']

class TeacherInline(admin.StackedInline):
    model = Teacher
    can_delete = False
    verbose_name_plural = '교사 정보'

# ★★★ ClassTeacher 모델을 Class Admin에 인라인으로 추가 ★★★
class ClassTeacherInline(admin.TabularInline):
    model = ClassTeacher
    extra = 1  # 기본으로 보여줄 추가 폼 개수
    autocomplete_fields = ['teacher'] # 교사 검색 기능 추가


class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = '학생 정보'

class CustomUserAdmin(UserAdmin):
    inlines = (TeacherInline, StudentInline)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# User 모델 재등록
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'employee_id', 'phone', 'created_at']
    list_filter = ['school', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    raw_id_fields = ['user']

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    # ★★★ [수정] list_display와 search_fields 변경 ★★★
    list_display = ['name', 'school', 'grade', 'class_number', 'get_main_teacher_name', 'student_count']
    list_filter = ['school', 'grade']
    search_fields = ['name', 'teachers__user__username'] # 'teacher' -> 'teachers'
    inlines = [ClassTeacherInline] # 인라인 추가

    def student_count(self, obj):
        return obj.student_set.count()
    student_count.short_description = '학생 수'

    def get_main_teacher_name(self, obj):
        main_teacher = obj.get_main_teacher()
        return main_teacher.user.get_full_name() if main_teacher else '미지정'
    get_main_teacher_name.short_description = '담임 교사'



@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    """(선택사항) ClassTeacher 모델을 직접 관리할 경우"""
    list_display = ['class_instance', 'teacher', 'role']
    list_filter = ['role']
    search_fields = ['class_instance__name', 'teacher__user__username']

# @admin.register(Class)
# class ClassAdmin(admin.ModelAdmin):
#     list_display = ['name', 'school', 'grade', 'class_number', 'teacher', 'student_count']
#     list_filter = ['school', 'grade', 'created_at']
#     search_fields = ['name', 'teacher__user__username']
    
#     def student_count(self, obj):
#         return obj.student_set.count()
#     student_count.short_description = '학생 수'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'school_class', 'student_id', 'birth_date', 'created_at']
    list_filter = ['school_class__school', 'school_class__grade', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'student_id']
    raw_id_fields = ['user']