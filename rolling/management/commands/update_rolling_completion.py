from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import Student
from student.models import StudentProgress
from teacher.models import ChasiSlide
from rolling.models import RollingAttempt


class Command(BaseCommand):
    help = '5회 시도를 완료한 학생들의 StudentProgress를 완료 상태로 업데이트 (롤링 컨텐츠 - 슬라이드 55)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 업데이트 없이 대상 학생들만 조회',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        ROLLING_SLIDE_ID = 55  # 롤링 컨텐츠 슬라이드 ID
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드: 실제 데이터 변경 없음'))
        
        self.stdout.write(f"롤링 컨텐츠 슬라이드 ID: {ROLLING_SLIDE_ID}")
        
        # 5회 시도를 모두 실패한 학생들 찾기
        students_with_5_failed_attempts = []
        
        # 5회차 시도가 있는 학생들 중에서
        students_with_attempt_5 = Student.objects.filter(
            rolling_attempts__attempt_number=5
        ).distinct()
        
        for student in students_with_attempt_5:
            attempts = RollingAttempt.objects.filter(student=student).order_by('attempt_number')
            
            # 정확히 5회 시도하고 모두 실패한 경우
            if attempts.count() == 5 and not attempts.filter(is_success=True).exists():
                # 해당 학생의 슬라이드 55 StudentProgress 확인
                try:
                    progress = StudentProgress.objects.get(
                        student=student,
                        slide_id=ROLLING_SLIDE_ID,
                        is_completed=False
                    )
                    students_with_5_failed_attempts.append({
                        'student': student,
                        'progress': progress,
                        'attempts_count': attempts.count()
                    })
                except StudentProgress.DoesNotExist:
                    # 해당 슬라이드의 진행상황이 없거나 이미 완료된 경우
                    continue
        
        self.stdout.write(f"\n5회 시도 완료 후 미완료 상태인 학생 수: {len(students_with_5_failed_attempts)}")
        
        if students_with_5_failed_attempts:
            self.stdout.write("\n대상 학생 목록:")
            for item in students_with_5_failed_attempts:
                student = item['student']
                progress = item['progress']
                self.stdout.write(f"- {student.user.get_full_name()} ({student.student_id}) - 슬라이드 {progress.slide.slide_number}")
        
        if not dry_run and students_with_5_failed_attempts:
            # 실제 업데이트 수행
            updated_count = 0
            
            with transaction.atomic():
                for item in students_with_5_failed_attempts:
                    progress = item['progress']
                    progress.is_completed = True
                    progress.completed_at = timezone.now()
                    if not progress.started_at:
                        progress.started_at = timezone.now()
                    progress.save()
                    updated_count += 1
                    
                    self.stdout.write(f"업데이트: {item['student'].user.get_full_name()} - 슬라이드 {progress.slide.slide_number}")
            
            self.stdout.write(
                self.style.SUCCESS(f'\n성공적으로 {updated_count}명의 학생 진행 상황을 완료로 업데이트했습니다.')
            )
        elif dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN 모드: 실제 업데이트를 수행하려면 --dry-run 옵션을 제거하세요.')
            )
        else:
            self.stdout.write(self.style.SUCCESS('\n업데이트할 대상이 없습니다.'))