"""
Django management command to sync HealthHabitTracker submission status with StudentProgress.
This fixes historical data where students submitted before StudentProgress integration was added.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from app_home.models import HealthHabitTracker
from student.models import StudentProgress


class Command(BaseCommand):
    help = 'Sync submitted HealthHabitTracker records with StudentProgress to mark them as completed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be updated without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information for each record'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write("=" * 70)
        self.stdout.write(
            self.style.SUCCESS(
                "건강습관 제출 데이터와 StudentProgress 동기화 시작"
            )
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN MODE] 실제 변경사항은 적용되지 않습니다."))
        self.stdout.write("=" * 70)
        
        # 제출된 모든 HealthHabitTracker 조회
        submitted_trackers = HealthHabitTracker.objects.filter(
            is_submitted=True
        ).select_related('student', 'slide')
        
        total_count = submitted_trackers.count()
        self.stdout.write(f"\n제출된 건강습관 기록 수: {total_count}개")
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING("동기화할 데이터가 없습니다."))
            return
        
        # 통계 변수
        created_count = 0
        updated_count = 0
        already_completed_count = 0
        error_count = 0
        
        with transaction.atomic():
            for tracker in submitted_trackers:
                try:
                    # StudentProgress 조회 또는 생성
                    progress, created = StudentProgress.objects.get_or_create(
                        student=tracker.student,
                        slide=tracker.slide,
                        defaults={
                            'started_at': tracker.created_at,
                            'is_completed': True,
                            'completed_at': tracker.submitted_at or timezone.now()
                        }
                    )
                    
                    if created:
                        created_count += 1
                        status = "새로 생성됨"
                        if not dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ StudentProgress 생성: {tracker.student.user.get_full_name()} - "
                                    f"슬라이드 {tracker.slide.slide_number}"
                                )
                            )
                    else:
                        # 이미 존재하는 경우
                        if progress.is_completed:
                            already_completed_count += 1
                            status = "이미 완료됨"
                        else:
                            # 완료되지 않은 경우만 업데이트
                            if not dry_run:
                                progress.is_completed = True
                                # completed_at이 없는 경우만 설정
                                if not progress.completed_at:
                                    progress.completed_at = tracker.submitted_at or timezone.now()
                                progress.save()
                            updated_count += 1
                            status = "완료로 업데이트"
                            if not dry_run:
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"✅ StudentProgress 업데이트: {tracker.student.user.get_full_name()} - "
                                        f"슬라이드 {tracker.slide.slide_number}"
                                    )
                                )
                    
                    if verbose:
                        self.stdout.write(
                            f"  학생: {tracker.student.user.get_full_name()} "
                            f"({tracker.student.student_id})"
                        )
                        self.stdout.write(
                            f"  슬라이드: {tracker.slide.slide_number} - "
                            f"{tracker.slide.chasi.chasi_title}"
                        )
                        self.stdout.write(
                            f"  제출일: {tracker.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if tracker.submitted_at else 'N/A'}"
                        )
                        self.stdout.write(f"  상태: {status}")
                        self.stdout.write("-" * 50)
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ 오류 발생 - 학생: {tracker.student.user.get_full_name()}, "
                            f"슬라이드: {tracker.slide.slide_number}, "
                            f"오류: {str(e)}"
                        )
                    )
            
            # Dry run인 경우 트랜잭션 롤백
            if dry_run:
                transaction.set_rollback(True)
        
        # 결과 요약
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("동기화 결과 요약"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"전체 제출된 기록: {total_count}개")
        self.stdout.write(f"새로 생성됨: {created_count}개")
        self.stdout.write(f"완료로 업데이트됨: {updated_count}개")
        self.stdout.write(f"이미 완료 상태: {already_completed_count}개")
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"오류 발생: {error_count}개"))
        
        if dry_run:
            self.stdout.write("\n" + self.style.WARNING(
                "🔍 DRY RUN 완료 - 실제 데이터는 변경되지 않았습니다."
            ))
            self.stdout.write(self.style.WARNING(
                "실제로 적용하려면 --dry-run 옵션 없이 다시 실행하세요."
            ))
        else:
            self.stdout.write("\n" + self.style.SUCCESS(
                f"✅ 동기화 완료! "
                f"{created_count + updated_count}개의 StudentProgress가 업데이트되었습니다."
            ))