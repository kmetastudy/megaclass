from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class School(models.Model):
    """학교 정보"""
    name = models.CharField(max_length=100, verbose_name="학교명")
    address = models.TextField(verbose_name="주소")
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
    """학급 정보"""
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="담당교사")
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'grade': self.grade,
            'class_number': self.class_number,
            'name': self.name,
            'teacher_name': self.teacher.user.get_full_name(),
            'student_count': self.student_set.count()
        }

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

# === 코스 관련 모델들 ===

class Course(models.Model):
    """코스 모델 (과목)"""
    subject_name = models.CharField(max_length=100, verbose_name="과목명")
    target = models.CharField(max_length=100, verbose_name="대상")
    description = models.TextField(blank=True, verbose_name="설명")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="담당교사")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "코스"
        verbose_name_plural = "코스들"
    
    def __str__(self):
        return f"{self.subject_name} - {self.target}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject_name': self.subject_name,
            'target': self.target,
            'description': self.description,
            'teacher_name': self.teacher.user.get_full_name(),
            'chapter_count': self.chapter_set.count(),
            'created_at': self.created_at.isoformat()
        }

class Chapter(models.Model):
    """대단원 모델"""
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="과목")
    chapter_title = models.CharField(max_length=200, verbose_name="대단원명")
    chapter_order = models.IntegerField(verbose_name="대단원 순서")
    
    class Meta:
        verbose_name = "대단원"
        verbose_name_plural = "대단원들"
        unique_together = ['subject', 'chapter_order']
        ordering = ['chapter_order']
    
    def __str__(self):
        return f"{self.subject.subject_name} - {self.chapter_title}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'chapter_title': self.chapter_title,
            'chapter_order': self.chapter_order,
            'subject_name': self.subject.subject_name,
            'sub_chapter_count': self.subchapter_set.count()
        }

class SubChapter(models.Model):
    """소단원 모델"""
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="과목")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, verbose_name="대단원")
    sub_chapter_title = models.CharField(max_length=200, verbose_name="소단원명")
    sub_chapter_order = models.IntegerField(verbose_name="소단원 순서")
    
    class Meta:
        verbose_name = "소단원"
        verbose_name_plural = "소단원들"
        unique_together = ['chapter', 'sub_chapter_order']
        ordering = ['sub_chapter_order']
    
    def __str__(self):
        return f"{self.chapter.chapter_title} - {self.sub_chapter_title}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'sub_chapter_title': self.sub_chapter_title,
            'sub_chapter_order': self.sub_chapter_order,
            'chapter_title': self.chapter.chapter_title,
            'chasi_count': self.chasi_set.count()
        }

class Chasi(models.Model):
    """차시 모델 (주제)"""
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="과목")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, verbose_name="대단원")
    chapter_order = models.IntegerField(verbose_name="대단원 순서")
    sub_chapter = models.ForeignKey(SubChapter, on_delete=models.CASCADE, verbose_name="소단원")
    sub_chapter_order = models.IntegerField(verbose_name="소단원 순서")
    chasi_title = models.CharField(max_length=200, verbose_name="차시명")
    chasi_order = models.IntegerField(verbose_name="차시 순서")
    description = models.TextField(blank=True, verbose_name="차시 설명")
    
    class Meta:
        verbose_name = "차시"
        verbose_name_plural = "차시들"
        unique_together = ['sub_chapter', 'chasi_order']
        ordering = ['chasi_order']
    
    def __str__(self):
        return f"{self.sub_chapter.sub_chapter_title} - {self.chasi_title}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'chasi_title': self.chasi_title,
            'chasi_order': self.chasi_order,
            'description': self.description,
            'subject_name': self.subject.subject_name,
            'chapter_title': self.chapter.chapter_title,
            'sub_chapter_title': self.sub_chapter.sub_chapter_title,
            'slide_count': self.chasiSlide_set.count()
        }

class ContentType(models.Model):
    """컨텐츠 타입 모델"""
    type_name = models.CharField(max_length=50, unique=True, verbose_name="타입명")
    description = models.TextField(blank=True, verbose_name="설명")
    
    class Meta:
        verbose_name = "컨텐츠 타입"
        verbose_name_plural = "컨텐츠 타입들"
    
    def __str__(self):
        return self.type_name
    
    def to_dict(self):
        return {
            'id': self.id,
            'type_name': self.type_name,
            'description': self.description
        }

class Contents(models.Model):
    """컨텐츠 모델"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name="컨텐츠 타입")
    title = models.CharField(max_length=200, verbose_name="제목")
    page = models.TextField(verbose_name="페이지 내용(HTML)")
    meta_data = models.JSONField(default=dict, verbose_name="메타데이터(루브릭)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "컨텐츠"
        verbose_name_plural = "컨텐츠들"
    
    def __str__(self):
        return f"{self.content_type.type_name} - {self.title}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content_type': self.content_type.type_name,
            'page': self.page,
            'meta_data': self.meta_data,
            'created_at': self.created_at.isoformat()
        }

class ContentsAttached(models.Model):
    """컨텐츠 첨부파일 모델"""
    contents = models.ForeignKey(Contents, on_delete=models.CASCADE, verbose_name="컨텐츠")
    file = models.FileField(upload_to='contents_files/', verbose_name="파일")
    file_type = models.CharField(max_length=50, verbose_name="파일 타입")
    original_name = models.CharField(max_length=200, verbose_name="원본 파일명")
    file_size = models.IntegerField(verbose_name="파일 크기")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "컨텐츠 첨부파일"
        verbose_name_plural = "컨텐츠 첨부파일들"
    
    def __str__(self):
        return f"{self.contents.title} - {self.original_name}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_url': self.file.url if self.file else None,
            'file_type': self.file_type,
            'original_name': self.original_name,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat()
        }

class ChasiSlide(models.Model):
    """차시 슬라이드 모델"""
    chasi = models.ForeignKey(Chasi, on_delete=models.CASCADE, verbose_name="차시")
    slide_number = models.IntegerField(verbose_name="슬라이드 번호")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name="컨텐츠 타입")
    content = models.ForeignKey(Contents, on_delete=models.CASCADE, verbose_name="컨텐츠")
    
    class Meta:
        verbose_name = "차시 슬라이드"
        verbose_name_plural = "차시 슬라이드들"
        unique_together = ['chasi', 'slide_number']
        ordering = ['slide_number']
    
    def __str__(self):
        return f"{self.chasi.chasi_title} - 슬라이드 {self.slide_number}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'slide_number': self.slide_number,
            'chasi_title': self.chasi.chasi_title,
            'content_type': self.content_type.type_name,
            'content': self.content.to_dict()
        }

# === 코스 할당 및 진행 관련 모델들 ===

class CourseAssignment(models.Model):
    """코스 할당 모델"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="코스")
    assigned_class = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True, verbose_name="할당 학급")
    assigned_student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, verbose_name="할당 학생")
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="마감일")
    
    class Meta:
        verbose_name = "코스 할당"
        verbose_name_plural = "코스 할당들"
    
    def __str__(self):
        target = self.assigned_class.name if self.assigned_class else self.assigned_student.user.get_full_name()
        return f"{self.course.subject_name} -> {target}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_name': self.course.subject_name,
            'assigned_to': self.assigned_class.name if self.assigned_class else self.assigned_student.user.get_full_name(),
            'assignment_type': 'class' if self.assigned_class else 'individual',
            'assigned_date': self.assigned_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None
        }

class StudentProgress(models.Model):
    """학생 진행 상황 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
    chasi = models.ForeignKey(Chasi, on_delete=models.CASCADE, verbose_name="차시")
    slide = models.ForeignKey(ChasiSlide, on_delete=models.CASCADE, verbose_name="슬라이드")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="시작 시간")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="완료 시간")
    is_completed = models.BooleanField(default=False, verbose_name="완료 여부")
    
    class Meta:
        verbose_name = "학생 진행 상황"
        verbose_name_plural = "학생 진행 상황들"
        unique_together = ['student', 'slide']
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student.user.get_full_name(),
            'chasi_title': self.chasi.chasi_title,
            'slide_number': self.slide.slide_number,
            'is_completed': self.is_completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class StudentAnswer(models.Model):
    """학생 답안 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
    slide = models.ForeignKey(ChasiSlide, on_delete=models.CASCADE, verbose_name="슬라이드")
    answer_data = models.JSONField(default=dict, verbose_name="답안 데이터")
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(null=True, blank=True, verbose_name="정답 여부")
    score = models.FloatField(null=True, blank=True, verbose_name="점수")
    feedback = models.TextField(blank=True, verbose_name="피드백")
    
    class Meta:
        verbose_name = "학생 답안"
        verbose_name_plural = "학생 답안들"
        unique_together = ['student', 'slide']
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student.user.get_full_name(),
            'slide_title': f"{self.slide.chasi.chasi_title} - 슬라이드 {self.slide.slide_number}",
            'answer_data': self.answer_data,
            'is_correct': self.is_correct,
            'score': self.score,
            'feedback': self.feedback,
            'submitted_at': self.submitted_at.isoformat()
        }

class StudentRecord(models.Model):
    """학생 수행 기록 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
    slide = models.ForeignKey(ChasiSlide, on_delete=models.CASCADE, verbose_name="슬라이드")
    session_number = models.IntegerField(default=1, verbose_name="회차")
    record_data = models.JSONField(default=dict, verbose_name="기록 데이터")
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "학생 수행 기록"
        verbose_name_plural = "학생 수행 기록들"
        unique_together = ['student', 'slide', 'session_number']
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student.user.get_full_name(),
            'slide_title': f"{self.slide.chasi.chasi_title} - 슬라이드 {self.slide.slide_number}",
            'session_number': self.session_number,
            'record_data': self.record_data,
            'recorded_at': self.recorded_at.isoformat()
        }
