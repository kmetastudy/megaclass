from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import Student, Teacher, Class

class RollingAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='rolling_attempts')
    attempt_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_success = models.BooleanField()
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'attempt_number']
        ordering = ['attempt_number']
        verbose_name = '앞구르기 시도'
        verbose_name_plural = '앞구르기 시도들'
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.attempt_number}회차 - {'성공' if self.is_success else '실패'}"

class FeedbackCategory(models.Model):
    category_name = models.CharField(max_length=100)
    is_success_category = models.BooleanField()
    keywords = models.TextField(help_text="쉼표로 구분된 키워드")
    
    class Meta:
        verbose_name = '피드백 카테고리'
        verbose_name_plural = '피드백 카테고리들'
    
    def __str__(self):
        return self.category_name

class RollingEvaluation(models.Model):
    """교사가 학생의 전체 수행을 평가"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='rolling_evaluation')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    
    GRADE_CHOICES = [
        ('A', '🏆 최우수'),
        ('B', '🥇 우수'),
        ('C', '🥈 보통'),
        ('D', '🥉 노력 필요'),
    ]
    grade = models.CharField('등급', max_length=1, choices=GRADE_CHOICES)
    
    overall_feedback = models.TextField('종합 피드백')
    evaluated_at = models.DateTimeField('평가일', auto_now_add=True)
    
    class Meta:
        verbose_name = '앞구르기 종합 평가'
        verbose_name_plural = '앞구르기 종합 평가들'
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_grade_display()}"