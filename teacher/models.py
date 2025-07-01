from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Teacher, Class, Student
from django.apps import apps

class Course(models.Model):
    """코스 모델"""
    subject_name = models.CharField('과목명', max_length=100)
    target = models.CharField('대상', max_length=100)
    description = models.TextField('설명', blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name='담당교사')
    is_active = models.BooleanField('활성화', default=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '코스'
        verbose_name_plural = '코스'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject_name} - {self.target}"

class Chapter(models.Model):
    """대단원 모델"""
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='코스', related_name='chapters')
    chapter_title = models.CharField('대단원명', max_length=200)
    chapter_order = models.PositiveIntegerField('순서', default=1)
    description = models.TextField('설명', blank=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '대단원'
        verbose_name_plural = '대단원'
        ordering = ['subject', 'chapter_order']
        unique_together = ['subject', 'chapter_order']
    
    def __str__(self):
        return f"{self.subject.subject_name} - {self.chapter_title}"

class SubChapter(models.Model):
    """소단원 모델"""
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='코스')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, verbose_name='대단원', related_name='subchapters')
    sub_chapter_title = models.CharField('소단원명', max_length=200)
    sub_chapter_order = models.PositiveIntegerField('순서', default=1)
    description = models.TextField('설명', blank=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '소단원'
        verbose_name_plural = '소단원'
        ordering = ['chapter', 'sub_chapter_order']
        unique_together = ['chapter', 'sub_chapter_order']
    
    def __str__(self):
        return f"{self.chapter.chapter_title} - {self.sub_chapter_title}"
    
class ContentTypeCategory(models.Model):
    category_name=models.CharField('카테고리',max_length=100)
    description=  models.TextField('카테고리 설명', blank=True,null=True)
    icon = models.CharField('아이콘', max_length=50, blank=True,null=True)
    color = models.CharField('색상', max_length=7, blank=True,null=True)   
    
    class Meta:
        verbose_name = '컨텐츠 카테고리'
        verbose_name_plural = '컨텐츠 카테고리'
    
    def __str__(self):
        return self.category_name
    

class ContentType(models.Model):
    """컨텐츠 타입 모델"""
    type_name = models.CharField('타입명', max_length=50)
    category_name=models.ForeignKey(ContentTypeCategory, on_delete=models.CASCADE, verbose_name='콘텐츠 카테고리',null=True,blank=True)
    description = models.TextField('설명', blank=True)
    icon = models.CharField('아이콘', max_length=50, blank=True,null=True)
    color = models.CharField('색상', max_length=7, blank=True,null=True)
    is_active = models.BooleanField('활성화', default=True)
    
    class Meta:
        verbose_name = '컨텐츠 타입'
        verbose_name_plural = '컨텐츠 타입'
    
    def __str__(self):
        return self.type_name

class Contents(models.Model):
    """콘텐츠 모델"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='콘텐츠 타입')
    title = models.CharField('제목', max_length=200)
    page = models.TextField('콘텐츠 페이지', help_text='HTML 형식의 콘텐츠')
    answer = models.TextField('정답', blank=True,null=True, help_text='객관식/단답형의 경우 정답')
    meta_data = models.JSONField('메타데이터', default=dict, blank=True)
    tags = models.JSONField('태그/평가기준', default=dict, blank=True, help_text='채점이나 평가 기준')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='생성자')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    is_active = models.BooleanField('활성화', default=True)
    is_public = models.BooleanField('공개', default=True, help_text='다른 교사들도 사용할 수 있도록 공개')  # 추가
    view_count = models.PositiveIntegerField('조회수', default=0)  # 이 줄 추가
    
    class Meta:
        verbose_name = '콘텐츠'
        verbose_name_plural = '콘텐츠'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.content_type.type_name} - {self.title}"
    
    def get_preview(self, length=100):
        """콘텐츠 미리보기 텍스트 반환"""
        import re
        text = re.sub('<[^<]+?>', '', self.page)
        return text[:length] + '...' if len(text) > length else text

class Chasi(models.Model):
    """차시 모델"""
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='코스')  # course 대신 subject로 통일
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, verbose_name='대단원')
    sub_chapter = models.ForeignKey(SubChapter, on_delete=models.CASCADE, verbose_name='소단원', related_name='chasis')
    chasi_title = models.CharField('차시명', max_length=200)  # 기존 코드와 호환성을 위해 chasi_title 유지
    chasi_order = models.PositiveIntegerField('순서', default=1)
    chapter_order = models.PositiveIntegerField('대단원 순서', default=1)
    sub_chapter_order = models.PositiveIntegerField('소단원 순서', default=1)
    description = models.TextField('설명', blank=True)
    learning_objectives = models.TextField('학습목표', blank=True)
    duration_minutes = models.PositiveIntegerField('수업시간(분)', default=45)
    is_published = models.BooleanField('공개', default=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '차시'
        verbose_name_plural = '차시'
        ordering = ['sub_chapter', 'chasi_order']
        unique_together = ['sub_chapter', 'chasi_order']
    
    def __str__(self):
        return f"{self.sub_chapter.sub_chapter_title} - {self.chasi_title}"
    
    # 호환성을 위한 프로퍼티 추가
    @property
    def title(self):
        return self.chasi_title
    
    @property
    def slides(self):
        """기존 코드 호환성을 위한 slides 프로퍼티"""
        return self.teacher_slides.all()

class ChasiSlide(models.Model):
    """차시 슬라이드 모델"""
    chasi = models.ForeignKey(Chasi, on_delete=models.CASCADE, verbose_name='차시', related_name='teacher_slides')
    slide_number = models.PositiveIntegerField('슬라이드 번호')
    slide_title = models.CharField('슬라이드 제목', max_length=200, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='컨텐츠 타입')
    content = models.ForeignKey(Contents, on_delete=models.CASCADE, verbose_name='컨텐츠')
    instructor_notes = models.TextField('강사 노트', blank=True)
    estimated_time = models.PositiveIntegerField('예상 시간(분)', default=5)
    is_active = models.BooleanField('활성화', default=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '차시 슬라이드'
        verbose_name_plural = '차시 슬라이드'
        ordering = ['chasi', 'slide_number']
        unique_together = ['chasi', 'slide_number']
    
    def __str__(self):
        return f"{self.id}-{self.chasi.chasi_title} - 슬라이드 {self.slide_number}"
    


# models.py에 추가
from django.core.exceptions import ValidationError
class CourseAssignment(models.Model):
    """코스 할당 모델"""
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='assignments')
    
    # accounts 앱의 모델들을 참조
    assigned_class = models.ForeignKey(
        'accounts.Class',  # accounts 앱의 Class 모델
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='course_assignments'
    )
    assigned_student = models.ForeignKey(
        'accounts.Student',  # accounts 앱의 Student 모델
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='course_assignments'
    )
    
    # 할당 정보
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'teacher_course_assignment'
        verbose_name = '코스 할당'
        verbose_name_plural = '코스 할당'
        # 중복 할당 방지
        unique_together = [
            ('course', 'assigned_class'),
            ('course', 'assigned_student'),
        ]
        indexes = [
            models.Index(fields=['course', 'assigned_class']),
            models.Index(fields=['course', 'assigned_student']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        if self.assigned_class:
            return f"{self.course.subject_name} - {self.assigned_class.name}"
        elif self.assigned_student:
            return f"{self.course.subject_name} - {self.assigned_student.user.get_full_name()}"
        return f"{self.course.subject_name} - 미할당"
    
    def clean(self):
        """검증: 학급과 학생 중 하나만 선택되어야 함"""
        if self.assigned_class and self.assigned_student:
            raise ValidationError('학급과 학생 중 하나만 선택할 수 있습니다.')
        if not self.assigned_class and not self.assigned_student:
            raise ValidationError('학급 또는 학생을 선택해야 합니다.')
    
    def get_assigned_to(self):
        """할당 대상 반환"""
        if self.assigned_class:
            return self.assigned_class
        return self.assigned_student
    
    def get_student_count(self):
        """할당된 학생 수 반환"""
        if self.assigned_class:
            return self.assigned_class.student_set.count()
        return 1 if self.assigned_student else 0



# ContentsAttached 모델 (기존에 있다면 수정, 없다면 추가)
class ContentsAttached(models.Model):
    """컨텐츠 첨부파일 모델"""
    contents = models.ForeignKey(
        Contents, 
        on_delete=models.CASCADE, 
        verbose_name='컨텐츠', 
        related_name='attachments',
        null=True,  # 임시 업로드를 위해 null 허용
        blank=True
    )
    file = models.FileField('파일', upload_to='contents/attachments/%Y/%m/')
    original_name = models.CharField('원본 파일명', max_length=255)
    file_type = models.CharField('파일 타입', max_length=50)
    file_size = models.PositiveIntegerField('파일 크기(bytes)')
    uploaded_at = models.DateTimeField('업로드일', auto_now_add=True)
    
    # 추가 필드들
    is_temporary = models.BooleanField('임시 파일', default=True, help_text='임시 업로드 파일인지 여부')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='업로드 사용자', null=True)
    
    class Meta:
        verbose_name = '컨텐츠 첨부파일'
        verbose_name_plural = '컨텐츠 첨부파일'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['contents', 'uploaded_at']),
            models.Index(fields=['is_temporary', 'uploaded_at']),
        ]
    
    def __str__(self):
        if self.contents:
            return f"{self.contents.title} - {self.original_name}"
        return f"임시 파일 - {self.original_name}"

    def delete(self, *args, **kwargs):
        """파일 삭제 시 실제 파일도 함께 삭제"""
        if self.file:
            try:
                self.file.delete(save=False)
            except Exception as e:
                print(f"파일 삭제 오류: {e}")
        super().delete(*args, **kwargs)


# class ContentsAttached_0628(models.Model):
#     """컨텐츠 첨부파일 모델"""
#     contents = models.ForeignKey(Contents, on_delete=models.CASCADE, verbose_name='컨텐츠', related_name='attachments')
#     file = models.FileField('파일', upload_to='contents/attachments/%Y/%m/')
#     original_name = models.CharField('원본 파일명', max_length=255)
#     file_type = models.CharField('파일 타입', max_length=50)
#     file_size = models.PositiveIntegerField('파일 크기(bytes)')
#     uploaded_at = models.DateTimeField('업로드일', auto_now_add=True)
    
#     class Meta:
#         verbose_name = '컨텐츠 첨부파일'
#         verbose_name_plural = '컨텐츠 첨부파일'
#         ordering = ['-uploaded_at']
    
#     def __str__(self):
#         return f"{self.contents.title} - {self.original_name}"