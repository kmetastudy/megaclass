from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Student, Teacher, Class
from teacher.models import Contents, ContentType, ChasiSlide
import json

class NCSCompetency(models.Model):
    """NCS 역량 정의 모델"""
    code = models.CharField('역량코드', max_length=20, unique=True)
    main_category = models.CharField('대분류', max_length=100)
    sub_category = models.CharField('중분류', max_length=100)
    competency_name = models.CharField('역량명', max_length=200)
    description = models.TextField('설명', blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    level = models.IntegerField('레벨', default=1)  # 1: 대분류, 2: 중분류, 3: 세분류
    order = models.IntegerField('순서', default=0)
    is_active = models.BooleanField('활성화', default=True)
    
    class Meta:
        verbose_name = 'NCS 역량'
        verbose_name_plural = 'NCS 역량'
        ordering = ['level', 'order', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.competency_name}"


class NCSLearningSession(models.Model):
    """NCS 학습 세션 모델"""
    SESSION_TYPE_CHOICES = [
        ('auto', '자동 추천'),
        ('manual', '수동 선택'),
        ('weakness', '취약점 보강'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='학생')
    session_type = models.CharField('세션 타입', max_length=20, choices=SESSION_TYPE_CHOICES)
    competencies = models.ManyToManyField(NCSCompetency, verbose_name='대상 역량')
    total_questions = models.IntegerField('총 문항 수', default=0)
    completed_questions = models.IntegerField('완료 문항 수', default=0)
    correct_answers = models.IntegerField('정답 수', default=0)
    score = models.FloatField('점수', default=0.0)
    started_at = models.DateTimeField('시작 시간', default=timezone.now)
    completed_at = models.DateTimeField('완료 시간', null=True, blank=True)
    is_completed = models.BooleanField('완료 여부', default=False)
    time_spent = models.IntegerField('소요 시간(초)', default=0)
    
    class Meta:
        verbose_name = 'NCS 학습 세션'
        verbose_name_plural = 'NCS 학습 세션'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_session_type_display()} ({self.started_at.strftime('%Y-%m-%d')})"
    
    def calculate_score(self):
        if self.total_questions > 0:
            self.score = (self.correct_answers / self.total_questions) * 100
        return self.score




class NCSQuestion(models.Model):
    """NCS 학습 문항 모델"""
    session = models.ForeignKey(NCSLearningSession, on_delete=models.CASCADE, related_name='questions')
    content = models.ForeignKey(Contents, on_delete=models.CASCADE, verbose_name='콘텐츠')
    competency = models.ForeignKey(NCSCompetency, on_delete=models.CASCADE, verbose_name='역량')
    order = models.IntegerField('순서', default=0)
    is_answered = models.BooleanField('답변 여부', default=False)
    student_answer = models.CharField('학생 답안', max_length=10, blank=True)
    is_correct = models.BooleanField('정답 여부', null=True, blank=True)
    answered_at = models.DateTimeField('답변 시간', null=True, blank=True)
    time_spent = models.IntegerField('소요 시간(초)', default=0)
    # 재시도 관련 필드 추가
    max_attempts = models.IntegerField('최대 시도 횟수', default=3)
    current_attempt_count = models.IntegerField('현재 시도 횟수', default=0)
    
    class Meta:
        verbose_name = 'NCS 학습 문항'
        verbose_name_plural = 'NCS 학습 문항'
        ordering = ['session', 'order']
    
    def __str__(self):
        return f"{self.session} - 문항 {self.order}"
    
    def check_answer(self, answer):
        """답안 채점"""
        print(f"\n=== check_answer 메서드 ===")
        print(f"Student answer: {answer}")
        print(f"Content answer (raw): {self.content.answer}")
        
        self.student_answer = answer
        self.is_answered = True
        self.answered_at = timezone.now()
        
        # 정답 확인
        correct_answer = self.content.answer
        
        # JSON 형식인 경우 파싱
        if isinstance(correct_answer, str) and correct_answer.startswith('{'):
            try:
                import json
                parsed = json.loads(correct_answer)
                correct_answer = parsed.get('answer', correct_answer)
                print(f"Parsed correct answer: {correct_answer}")
            except:
                print("JSON parsing failed, using raw answer")
        
        self.is_correct = (str(answer) == str(correct_answer))
        print(f"Comparison: '{answer}' == '{correct_answer}' = {self.is_correct}")
        
        # 세션 업데이트
        if self.is_correct:
            self.session.correct_answers += 1
        self.session.completed_questions += 1
        self.session.save()
        
        self.save()
        
        print(f"Session progress: {self.session.completed_questions}/{self.session.total_questions}")
        print("=== check_answer 종료 ===\n")    
        return self.is_correct
    
    def check_answer_with_retry(self, answer, time_spent=0):
        """재시도 가능한 답안 채점"""
        print(f"\n=== check_answer_with_retry ===")
        
        # 시도 횟수 증가
        self.current_attempt_count += 1
        
        # 시도 기록 생성
        attempt = NCSQuestionAttempt.objects.create(
            question=self,
            student=self.session.student,
            attempt_number=self.current_attempt_count,
            answer=answer,
            time_spent=time_spent
        )
        
        # 정답 확인
        correct_answer = self.content.answer
        if isinstance(correct_answer, str) and correct_answer.startswith('{'):
            try:
                import json
                parsed = json.loads(correct_answer)
                correct_answer = parsed.get('answer', correct_answer)
            except:
                pass
        
        is_correct = (str(answer) == str(correct_answer))
        attempt.is_correct = is_correct
        attempt.save()
        
        # 정답인 경우 또는 최대 시도 횟수에 도달한 경우
        if is_correct or self.current_attempt_count >= self.max_attempts:
            self.student_answer = answer
            self.is_answered = True
            self.is_correct = is_correct
            self.answered_at = timezone.now()
            self.time_spent += time_spent
            
            # 세션 업데이트 (최초 정답 시에만)
            if is_correct and self.current_attempt_count == 1:
                self.session.correct_answers += 1
            
            # 완료 처리
            if self.current_attempt_count == 1:
                self.session.completed_questions += 1
                self.session.save()
        
        self.save()
        
        return {
            'is_correct': is_correct,
            'attempt_count': self.current_attempt_count,
            'can_retry': not is_correct and self.current_attempt_count < self.max_attempts,
            'correct_answer': correct_answer if not is_correct else None
        }
    
    def get_attempt_history(self):
        """시도 이력 조회"""
        return self.attempts.filter(student=self.session.student).order_by('attempt_number')


class NCSCompetencyAnalysis(models.Model):
    """NCS 역량별 분석 모델"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='학생')
    competency = models.ForeignKey(NCSCompetency, on_delete=models.CASCADE, verbose_name='역량')
    total_attempts = models.IntegerField('총 시도 횟수', default=0)
    correct_count = models.IntegerField('정답 횟수', default=0)
    incorrect_count = models.IntegerField('오답 횟수', default=0)
    accuracy_rate = models.FloatField('정답률', default=0.0)
    average_time = models.FloatField('평균 소요 시간(초)', default=0.0)
    last_attempt_date = models.DateTimeField('마지막 시도일', null=True, blank=True)
    weakness_score = models.FloatField('취약도 점수', default=0.0)  # 높을수록 취약
    updated_at = models.DateTimeField('업데이트일', auto_now=True)
    
    class Meta:
        verbose_name = 'NCS 역량 분석'
        verbose_name_plural = 'NCS 역량 분석'
        unique_together = ['student', 'competency']
        ordering = ['-weakness_score', 'competency__code']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.competency.competency_name} (정답률: {self.accuracy_rate:.1f}%)"
    
    def update_analysis(self):
        """분석 데이터 업데이트"""
        if self.total_attempts > 0:
            self.accuracy_rate = (self.correct_count / self.total_attempts) * 100
            # 취약도 점수 계산 (정답률이 낮고 시도 횟수가 많을수록 높음)
            self.weakness_score = (100 - self.accuracy_rate) * (1 + self.total_attempts * 0.1)
        self.save()


class NCSAssignment(models.Model):
    """NCS 과제 할당 모델"""
    ASSIGNMENT_TYPE_CHOICES = [
        ('individual', '개인별'),
        ('class', '반별'),
        ('weakness', '취약점 보강'),
    ]
    
    title = models.CharField('과제명', max_length=200)
    description = models.TextField('설명', blank=True)
    assignment_type = models.CharField('할당 타입', max_length=20, choices=ASSIGNMENT_TYPE_CHOICES)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name='교사')
    assigned_class = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True, verbose_name='할당 반')
    assigned_students = models.ManyToManyField(Student, blank=True, verbose_name='할당 학생')
    competencies = models.ManyToManyField(NCSCompetency, verbose_name='대상 역량')
    question_count = models.IntegerField('문항 수', default=10)
    due_date = models.DateTimeField('마감일', null=True, blank=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    is_active = models.BooleanField('활성화', default=True)
    
    class Meta:
        verbose_name = 'NCS 과제'
        verbose_name_plural = 'NCS 과제'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_assignment_type_display()})"


class NCSClassStatistics(models.Model):
    """반별 NCS 통계 모델"""
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name='반')
    competency = models.ForeignKey(NCSCompetency, on_delete=models.CASCADE, verbose_name='역량')
    average_accuracy = models.FloatField('평균 정답률', default=0.0)
    total_students = models.IntegerField('전체 학생 수', default=0)
    participated_students = models.IntegerField('참여 학생 수', default=0)
    average_attempts = models.FloatField('평균 시도 횟수', default=0.0)
    updated_at = models.DateTimeField('업데이트일', auto_now=True)
    
    class Meta:
        verbose_name = '반별 NCS 통계'
        verbose_name_plural = '반별 NCS 통계'
        unique_together = ['class_obj', 'competency']
    
    def __str__(self):
        return f"{self.class_obj.name} - {self.competency.competency_name}"
    


class NCSQuestionAttempt(models.Model):
    """NCS 문항별 시도 기록 모델"""
    question = models.ForeignKey(NCSQuestion, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='학생')
    attempt_number = models.IntegerField('시도 번호', default=1)
    answer = models.CharField('답안', max_length=10)
    is_correct = models.BooleanField('정답 여부', default=False)
    attempted_at = models.DateTimeField('시도 시간', auto_now_add=True)
    time_spent = models.IntegerField('소요 시간(초)', default=0)
    
    class Meta:
        verbose_name = 'NCS 문항 시도'
        verbose_name_plural = 'NCS 문항 시도'
        ordering = ['question', 'attempt_number']
        unique_together = ['question', 'student', 'attempt_number']
    
    def __str__(self):
        return f"{self.question} - 시도 {self.attempt_number}"


class NCSStudentAnswer(models.Model):
    """NCS 학생 답안 모델"""
    session = models.ForeignKey(NCSLearningSession, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(NCSQuestion, on_delete=models.CASCADE, related_name='student_answers')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.CharField('답안', max_length=10)
    is_correct = models.BooleanField('정답 여부', default=False)
    attempt_count = models.IntegerField('시도 횟수', default=1)
    time_spent = models.IntegerField('소요 시간(초)', default=0)
    submitted_at = models.DateTimeField('제출 시간', auto_now_add=True)
    
    class Meta:
        verbose_name = 'NCS 학생 답안'
        verbose_name_plural = 'NCS 학생 답안'
        unique_together = ['session', 'question', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - Q{self.question.order}"