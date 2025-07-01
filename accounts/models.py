from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class School(models.Model):
    """학교 정보"""
    name = models.CharField(max_length=100, verbose_name="학교명")
    address = models.TextField(verbose_name="주소")
    code = models.CharField(max_length=10, unique=True, default='SC001')  # 추가
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "학교"
        verbose_name_plural = "학교들"
    
    def __str__(self):
        return self.name
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'created_at': self.created_at.isoformat()
        }

class Teacher(models.Model):
    """교사 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="사번")
    phone = models.CharField(max_length=15, blank=True, verbose_name="전화번호")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "교사"
        verbose_name_plural = "교사들"
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.school.name})"
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.get_full_name(),
            'school_name': self.school.name,
            'employee_id': self.employee_id,
            'phone': self.phone,
            'created_at': self.created_at.isoformat()
        }

class Class(models.Model):
    """학급 정보 (수정됨)"""
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    # [제거] 기존 teacher 필드를 아래 ManyToManyField로 대체합니다.
    # teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="담당교사")
    
    # ★★★ [추가] 여러 교사를 역할과 함께 관리하기 위한 필드 ★★★
    teachers = models.ManyToManyField(
        Teacher,
        through='ClassTeacher',  # 아래 정의된 중간 모델을 사용
        related_name='classes',
        verbose_name="담당 교사들"
    )
    
    grade = models.IntegerField(verbose_name="학년")
    class_number = models.IntegerField(verbose_name="반")
    name = models.CharField(max_length=50, verbose_name="학급명")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "학급"
        verbose_name_plural = "학급들"
        unique_together = ['school', 'grade', 'class_number']
    
    def __str__(self):
        return f"{self.school.name} {self.grade}학년 {self.class_number}반"

    def get_main_teacher(self):
        """담임 교사를 반환하는 헬퍼 함수"""
        # 'main_teacher' 역할을 가진 교사를 우선적으로 반환
        main_teacher_relation = self.classteacher_set.filter(role='main_teacher').first()
        if main_teacher_relation:
            return main_teacher_relation.teacher
        return None # 담임이 없으면 None 반환


class ClassTeacher(models.Model):
    """★★★ [신규] 학급-교사 관계 및 역할 정의 모델 ★★★"""
    class RoleChoices(models.TextChoices):
        ADMIN_TEACHER = 'admin_teacher', '총괄 교사'
        MAIN_TEACHER = 'main_teacher', '담임 교사'
        SUBJECT_TEACHER = 'subject_teacher', '교과 교사'
        ASSISTANT = 'assistant', '부담임/보조 교사'
        ETC = 'etc', '기타'

    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="학급")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="교사")
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.MAIN_TEACHER,
        verbose_name="역할"
    )

    class Meta:
        verbose_name = "학급별 교사"
        verbose_name_plural = "학급별 교사 목록"
        unique_together = ('class_instance', 'teacher') # 한 교사는 한 학급에 하나의 역할만 가짐

    def __str__(self):
        return f"{self.class_instance} - {self.teacher.user.get_full_name()} ({self.get_role_display()})"



class Student(models.Model):
    """학생 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school_class = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="학급")
    student_id = models.CharField(max_length=20, verbose_name="학번")
    birth_date = models.DateField(verbose_name="생년월일")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "학생"
        verbose_name_plural = "학생들"
        unique_together = ['school_class', 'student_id']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.school_class})"
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.get_full_name(),
            'class_name': str(self.school_class),
            'student_id': self.student_id,
            'created_at': self.created_at.isoformat()
        }