# models.py
from django.db import models
from django.utils import timezone
from accounts.models import Student, Teacher
from teacher.models import ChasiSlide

class HealthHabitTracker(models.Model):
    """건강 습관 추적기 메인 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='health_habits')
    slide = models.ForeignKey(ChasiSlide, on_delete=models.CASCADE)
    
    # 6가지 약속
    promises = models.JSONField('약속 목록', default=dict)
    
    # 최종 소감
    final_reflection = models.TextField('최종 소감', blank=True)
    
    # 타임스탬프
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    submitted_at = models.DateTimeField('제출일', null=True, blank=True)
    
    # 상태
    is_submitted = models.BooleanField('제출 여부', default=False)
    
    class Meta:
        verbose_name = '건강 습관 기록'
        verbose_name_plural = '건강 습관 기록들'
        unique_together = ['student', 'slide']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()}의 건강 습관 기록"
    
    def get_completion_stats(self):
        """완료 통계 계산"""
        total_reflections = self.reflections.count()
        total_possible = 84  # 6 promises * 14 days
        completion_rate = (total_reflections / total_possible * 100) if total_possible > 0 else 0
        
        return {
            'total_reflections': total_reflections,
            'completion_rate': round(completion_rate, 1),
            'promises_stats': self.get_promise_stats()
        }
    
    def get_promise_stats(self):
        """약속별 통계"""
        stats = {}
        for i in range(1, 7):
            reflections = self.reflections.filter(promise_number=i)
            stats[i] = {
                'completed_days': reflections.count(),
                'rate': round((reflections.count() / 14) * 100, 1)
            }
        return stats


class DailyReflection(models.Model):
    """일일 실천 소감"""
    tracker = models.ForeignKey(HealthHabitTracker, on_delete=models.CASCADE, related_name='reflections')
    promise_number = models.IntegerField('약속 번호')
    week = models.IntegerField('주차')
    day = models.IntegerField('요일')
    
    reflection_text = models.TextField('소감')
    reflection_date = models.DateField('실천 날짜')
    reflection_time = models.TimeField('실천 시간')
    
    created_at = models.DateTimeField('작성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    # 평가 상태
    is_evaluated = models.BooleanField('평가 여부', default=False)
    
    class Meta:
        verbose_name = '일일 소감'
        verbose_name_plural = '일일 소감들'
        unique_together = ['tracker', 'promise_number', 'week', 'day']
        ordering = ['promise_number', 'week', 'day']
    
    def __str__(self):
        days = ['월', '화', '수', '목', '금', '토', '일']
        return f"{self.tracker.student.user.get_full_name()} - 약속{self.promise_number} {self.week}주 {days[self.day-1]}요일"


class DailyReflectionEvaluation(models.Model):
    """일일 소감 평가 모델"""
    reflection = models.OneToOneField(DailyReflection, on_delete=models.CASCADE, related_name='evaluation')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    
    # 평가 내용
    SCORE_CHOICES = [
        (3, '😊 매우 잘함'),
        (2, '😄 잘함'),
        (1, '😐 보통'),
    ]
    score = models.IntegerField('점수', choices=SCORE_CHOICES)
    
    # 이모지 피드백
    EMOJI_CHOICES = [
        ('great', '🌟'),
        ('good', '👍'),
        ('nice', '💪'),
        ('fighting', '🔥'),
        ('smile', '😊'),
    ]
    emoji_feedback = models.CharField('이모지', max_length=10, choices=EMOJI_CHOICES)
    
    # 짧은 코멘트
    comment = models.CharField('코멘트', max_length=100, blank=True)
    
    # 스탬프 (선택사항)
    has_stamp = models.BooleanField('스탬프 부여', default=False)
    
    evaluated_at = models.DateTimeField('평가일', auto_now_add=True)
    
    class Meta:
        verbose_name = '일일 소감 평가'
        verbose_name_plural = '일일 소감 평가들'
    
    def __str__(self):
        return f"{self.reflection} 평가"


class TrackerEvaluation(models.Model):
    """전체 건강 습관 종합 평가"""
    tracker = models.OneToOneField(HealthHabitTracker, on_delete=models.CASCADE, related_name='overall_evaluation')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    
    # 종합 평가
    GRADE_CHOICES = [
        ('A', '🏆 최우수'),
        ('B', '🥇 우수'),
        ('C', '🥈 보통'),
        ('D', '🥉 노력 필요'),
    ]
    grade = models.CharField('등급', max_length=1, choices=GRADE_CHOICES)
    
    # 종합 점수
    total_score = models.IntegerField('종합 점수', default=0)
    
    # 칭찬 뱃지
    BADGE_CHOICES = [
        ('perfect', '💯 완벽한 실천'),
        ('consistent', '📅 꾸준한 실천'),
        ('improved', '📈 발전하는 모습'),
        ('creative', '🎨 창의적인 소감'),
        ('positive', '☀️ 긍정적인 태도'),
    ]
    badges = models.JSONField('획득 뱃지', default=list)
    
    # 종합 피드백
    feedback = models.TextField('종합 피드백')
    
    evaluated_at = models.DateTimeField('평가일', auto_now_add=True)
    
    class Meta:
        verbose_name = '종합 평가'
        verbose_name_plural = '종합 평가들'
    
    def __str__(self):
        return f"{self.tracker} 종합 평가"