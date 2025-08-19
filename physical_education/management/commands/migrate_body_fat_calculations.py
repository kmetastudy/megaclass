import json
from decimal import Decimal, ROUND_UP
from django.core.management.base import BaseCommand
from django.db import transaction
from physical_education.models import PAPSRecord, PAPSActivity


class Command(BaseCommand):
    help = '기존 체지방률평가 PAPSRecord에 근육량/지방량 계산값 추가'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 업데이트 없이 미리보기만 실행',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드: 실제 업데이트는 하지 않습니다.'))
        
        self.stdout.write(self.style.SUCCESS('체지방률평가 데이터 마이그레이션을 시작합니다...'))
        
        # 체지방률평가 활동 조회
        try:
            body_fat_activity = PAPSActivity.objects.get(name='BODY_FAT_RATE_TEST')
        except PAPSActivity.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('체지방률평가 활동을 찾을 수 없습니다.')
            )
            return
        
        # 해당 활동의 모든 PAPSRecord 조회
        records = PAPSRecord.objects.filter(activity_id=body_fat_activity.id)
        
        if not records.exists():
            self.stdout.write(
                self.style.WARNING('체지방률평가 PAPSRecord가 없습니다.')
            )
            return
        
        self.stdout.write(f'총 {records.count()}개의 체지방률평가 기록을 확인합니다...')
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        with transaction.atomic():
            for record in records:
                try:
                    measurement_data = record.measurement_data or {}
                    
                    # 필수 데이터 확인
                    height = measurement_data.get('body_fat_rate_test_height')
                    weight = measurement_data.get('body_fat_rate_test_weight')
                    body_fat_rate = measurement_data.get('body_fat_rate')
                    
                    if not all([height, weight, body_fat_rate]):
                        self.stdout.write(
                            f'⚠️  학생 ID {record.student_id}: 필수 데이터 부족 (키: {height}, 체중: {weight}, 체지방률: {body_fat_rate})'
                        )
                        skipped_count += 1
                        continue
                    
                    # 이미 계산된 값이 있는지 확인
                    has_muscle_mass = 'body_fat_rate_muscle_mass' in measurement_data
                    has_fat_mass = 'body_fat_rate_fat_mass' in measurement_data
                    
                    if has_muscle_mass and has_fat_mass:
                        self.stdout.write(
                            f'ℹ️  학생 ID {record.student_id}: 이미 계산된 값 존재'
                        )
                        skipped_count += 1
                        continue
                    
                    # 계산 수행
                    weight_decimal = Decimal(str(weight))
                    body_fat_rate_decimal = Decimal(str(body_fat_rate))
                    
                    # 근육량(%) = 0.85 × 체중 - (체중 × 체지방률) / 100
                    muscle_mass = Decimal('0.85') * weight_decimal - (weight_decimal * body_fat_rate_decimal) / Decimal('100')
                    muscle_mass_rounded = (muscle_mass * Decimal('10')).quantize(Decimal('1'), rounding=ROUND_UP) / Decimal('10')
                    
                    # 지방량(%) = 체중 × 체지방률(%)
                    fat_mass = weight_decimal * body_fat_rate_decimal / Decimal('100')
                    fat_mass_rounded = (fat_mass * Decimal('10')).quantize(Decimal('1'), rounding=ROUND_UP) / Decimal('10')
                    
                    if dry_run:
                        self.stdout.write(
                            f'📋 학생 ID {record.student_id}: '
                            f'근육량 {float(muscle_mass_rounded)}%, '
                            f'지방량 {float(fat_mass_rounded)}% (계산 예정)'
                        )
                    else:
                        # 실제 업데이트
                        measurement_data['body_fat_rate_muscle_mass'] = float(muscle_mass_rounded)
                        measurement_data['body_fat_rate_fat_mass'] = float(fat_mass_rounded)
                        
                        record.measurement_data = measurement_data
                        record.save()
                        
                        self.stdout.write(
                            f'✅ 학생 ID {record.student_id}: '
                            f'근육량 {float(muscle_mass_rounded)}%, '
                            f'지방량 {float(fat_mass_rounded)}% 업데이트 완료'
                        )
                    
                    updated_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ 학생 ID {record.student_id}: 처리 실패 - {str(e)}')
                    )
                    error_count += 1
                    if not dry_run:
                        raise  # 트랜잭션 롤백을 위해 예외 재발생
        
        # 결과 요약
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== 마이그레이션 완료 ==='))
        
        if dry_run:
            self.stdout.write(f'📋 업데이트 대상: {updated_count}개')
            self.stdout.write(f'⚠️  건너뛴 항목: {skipped_count}개')
            self.stdout.write(f'❌ 오류 항목: {error_count}개')
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('실제 업데이트를 하려면 --dry-run 옵션을 제거하고 다시 실행하세요.'))
        else:
            self.stdout.write(f'✅ 성공적으로 업데이트: {updated_count}개')
            self.stdout.write(f'⚠️  건너뛴 항목: {skipped_count}개')
            self.stdout.write(f'❌ 실패한 항목: {error_count}개')
            
            if error_count == 0:
                self.stdout.write(self.style.SUCCESS('🎉 모든 체지방률평가 기록이 성공적으로 업데이트되었습니다!'))