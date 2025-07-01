from django.db import models
from accounts.models import Student
from teacher.models import Course, CourseAssignment
from teacher.models import ChasiSlide,Contents,ContentType

class StudentProgress(models.Model):
    """학생 진행 상황 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
    slide = models.ForeignKey('teacher.ChasiSlide', on_delete=models.CASCADE, verbose_name="슬라이드")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="시작 시간")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="완료 시간")
    is_completed = models.BooleanField(default=False, verbose_name="완료 여부")
    view_count = models.IntegerField(default=0, verbose_name="조회수")  # 추가
    
    class Meta:
        verbose_name = "학생 진행 상황"
        verbose_name_plural = "학생 진행 상황들"
        unique_together = ['student', 'slide']
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student.user.get_full_name(),
            'slide_number': self.slide.slide_number,
            'is_completed': self.is_completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    

class StudentAnswer(models.Model):
    """학생 답안 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
    slide = models.ForeignKey('teacher.ChasiSlide', on_delete=models.CASCADE, verbose_name="슬라이드")
    answer = models.JSONField(default=dict, verbose_name="답안 데이터")
    submitted_at = models.DateTimeField(auto_now=True)
    is_correct = models.BooleanField(null=True, blank=True, verbose_name="정답 여부")
    score = models.FloatField(null=True, blank=True, verbose_name="점수")
    feedback = models.TextField(blank=True, verbose_name="피드백")
    
    class Meta:
        verbose_name = "학생 답안"
        verbose_name_plural = "학생 답안들"
        unique_together = ['student', 'slide']
        ordering = ['-submitted_at']

    
    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student.user.get_full_name(),
            'slide_title': f"슬라이드 {self.slide.slide_number}",
            'answer': self.answer,
            'is_correct': self.is_correct,
            'score': self.score,
            'feedback': self.feedback,
            'submitted_at': self.submitted_at.isoformat()
        }

class StudentNote(models.Model):
    """학생 노트 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='학생')
    slide = models.ForeignKey(ChasiSlide, on_delete=models.CASCADE, verbose_name='슬라이드')
    content = models.TextField(verbose_name='노트 내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '학생 노트'
        verbose_name_plural = '학생 노트 목록'
        unique_together = ['student', 'slide']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.slide} 노트"
    

class PhysicalResultType(models.Model):
    type_code=models.CharField(max_length=100,null=True)
    type_name=models.CharField(max_length=100,default='달리기') 
    measure  = models.CharField(max_length=100,default='mili_second') 
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    class Meta:
        verbose_name = '기록 유형'
        verbose_name_plural = '기록 유형 목록'
        unique_together = ['type_code', 'type_name']
    
    def __str__(self):
        return f"{self.type_code} - {self.type_name} "

class StudentPhysicalResult(models.Model):
    """학생 기록 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
    slide = models.ForeignKey('teacher.ChasiSlide', on_delete=models.CASCADE, verbose_name="슬라이드")
    # record  = models.FloatField(default=0)
    record  = models.JSONField(default=dict, verbose_name="기록결과")
    writer= models.CharField(max_length=100,null=True,blank=True)
    score = models.FloatField(null=True, blank=True, verbose_name="점수")
    submitted_at = models.DateTimeField(auto_now=True,verbose_name='발생일')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
   
    
    class Meta:
        verbose_name = "학생 기록"
        verbose_name_plural = "학생 기록들"
        unique_together = ['student', 'slide']
        ordering = ['-submitted_at']

    
    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student.user.get_full_name(),
            'slide_title': f"슬라이드 {self.slide.slide_number}",
            'answer': self.answer,
            'is_correct': self.is_correct,
            'score': self.score,
            'feedback': self.feedback,
            'submitted_at': self.submitted_at.isoformat()
        }
    

# class StudentAssignedContent(models.Model):
#     """학생 자동 할당 모델"""
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
#     slide = models.ForeignKey('teacher.ChasiSlide', on_delete=models.CASCADE, verbose_name="슬라이드")
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='컨텐츠 타입')
#     content = models.ForeignKey(Contents, on_delete=models.CASCADE, verbose_name='컨텐츠')
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
#     updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
#     assigned_by=models.CharField(max_length=100,default='auto')
#     # answer = models.JSONField(default=dict, verbose_name="답안 데이터")
#     # submitted_at = models.DateTimeField(auto_now=True)
#     # is_correct = models.BooleanField(null=True, blank=True, verbose_name="정답 여부")
#     # score = models.FloatField(null=True, blank=True, verbose_name="점수")
#     # feedback = models.TextField(blank=True, verbose_name="피드백")

    
#     class Meta:
#         verbose_name = "학생 추천"
#         verbose_name_plural = "학생 추천들"
#         unique_together = ['student', 'slide','content']
#         ordering = ['-created_at']

    
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'student_name': self.student.user.get_full_name(),
#             'slide_title': f"슬라이드 {self.slide.slide_number}",
#             'content': f"{self.content.content_type}-{self.content.title}",
            
#         }
    
# class StudentAssignedAnswer(models.Model):
#     """학생 답안 모델"""
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
#     slide = models.ForeignKey('teacher.ChasiSlide', on_delete=models.CASCADE, verbose_name="슬라이드")
#     assigned_content=models.ForeignKey('StudentAssignedContent', on_delete=models.CASCADE, verbose_name="슬라이드컨텐츠")
#     answer = models.JSONField(default=dict, verbose_name="답안 데이터")
#     submitted_at = models.DateTimeField(auto_now=True)
#     is_correct = models.BooleanField(null=True, blank=True, verbose_name="정답 여부")
#     score = models.FloatField(null=True, blank=True, verbose_name="점수")
#     feedback = models.TextField(blank=True, verbose_name="피드백")
    
#     class Meta:
#         verbose_name = "학생 답안"
#         verbose_name_plural = "학생 답안들"
#         unique_together = ['student', 'slide']
#         ordering = ['-submitted_at']

    
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'student_name': self.student.user.get_full_name(),
#             'slide_title': f"슬라이드 {self.slide.slide_number}",
#             'content_title': f"컨텐츠 {self.assigned_content.title}",
#             'answer': self.answer,
#             'is_correct': self.is_correct,
#             'score': self.score,
#             'feedback': self.feedback,
#             'submitted_at': self.submitted_at.isoformat()
#         }