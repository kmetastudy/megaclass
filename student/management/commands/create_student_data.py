from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import School, Teacher, Class, Student
from teacher.models import Course, Chapter, SubChapter, Chasi, ChasiSlide, ContentType, Contents, CourseAssignment
from student.models import StudentProgress, StudentAnswer
from faker import Faker
import random
from datetime import timedelta

fake = Faker('ko_KR')

class Command(BaseCommand):
    help = '학생 학습 데이터 생성'

    def handle(self, *args, **options):
        self.stdout.write('학생 학습 데이터 생성 시작...')
        
        # 기존 데이터 확인
        if Student.objects.exists():
            students = Student.objects.all()
            self.stdout.write(f'기존 학생 {students.count()}명 사용')
        else:
            self.stdout.write('학생 데이터가 없습니다. 먼저 accounts 데이터를 생성하세요.')
            return
        
        # 코스 할당 확인
        assignments = CourseAssignment.objects.all()
        if not assignments.exists():
            self.stdout.write('코스 할당이 없습니다. teacher 앱에서 코스를 할당하세요.')
            return
        
        # 학습 진도 생성
        progress_count = 0
        answer_count = 0
        
        for student in students[:50]:  # 처음 50명만
            # 학생이 할당받은 코스 찾기
            student_assignments = CourseAssignment.objects.filter(
                Q(assigned_class=student.school_class) | Q(assigned_student=student),
                is_active=True
            )
            
            for assignment in student_assignments[:2]:  # 최대 2개 코스만
                # 해당 코스의 슬라이드들
                slides = ChasiSlide.objects.filter(
                    chasi__sub_chapter__chapter__subject=assignment.course,
                    is_active=True
                ).order_by('chasi__sub_chapter__chapter__chapter_order', 
                          'chasi__sub_chapter__sub_chapter_order',
                          'chasi__chasi_order',
                          'slide_number')
                
                # 진도율 (50~90%)
                progress_rate = random.uniform(0.5, 0.9)
                slides_to_study = int(slides.count() * progress_rate)
                
                start_date = timezone.now() - timedelta(days=30)
                
                for i, slide in enumerate(slides[:slides_to_study]):
                    # 학습 시작 시간 (순차적으로)
                    started_at = start_date + timedelta(
                        days=i // 5,  # 하루에 5개씩
                        hours=random.randint(9, 21),
                        minutes=random.randint(0, 59)
                    )
                    
                    progress = StudentProgress.objects.create(
                        student=student,
                        slide=slide,
                        started_at=started_at,
                        view_count=random.randint(1, 3)
                    )
                    
                    # 80% 확률로 완료
                    if random.random() < 0.8:
                        progress.is_completed = True
                        progress.completed_at = started_at + timedelta(
                            minutes=random.randint(5, 20)
                        )
                        progress.save()
                        
                        # 문제가 있는 경우 답안 제출
                        if slide.content.answer:
                            answer = StudentAnswer.objects.create(
                                student=student,
                                slide=slide,
                                answer=fake.sentence() if slide.content_type.type_name == '서술형' else slide.content.answer,
                                submitted_at=progress.completed_at
                            )
                            
                            # 객관식/단답형은 자동 채점
                            if slide.content_type.type_name in ['객관식', '단답형']:
                                answer.is_correct = random.random() < 0.7  # 70% 정답률
                                answer.score = 100 if answer.is_correct else 0
                                answer.save()
                            
                            answer_count += 1
                    
                    progress_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'''
        학생 학습 데이터 생성 완료!
        - 학습 진도: {progress_count}개
        - 제출 답안: {answer_count}개
        '''))