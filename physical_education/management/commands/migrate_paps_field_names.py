import json
from django.core.management.base import BaseCommand
from django.db import transaction
from physical_education.models import PAPSRecord, PAPSActivity


class Command(BaseCommand):
    help = 'PAPSRecord의 measurement_data 필드명을 새로운 구조로 마이그레이션'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 변경 없이 미리보기만 수행',
        )
        parser.add_argument(
            '--activity',
            type=str,
            help='특정 활동만 처리 (예: SHUTTLE_RUN)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        activity_filter = options['activity']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드: 실제 변경은 하지 않습니다.'))
        else:
            self.stdout.write(self.style.SUCCESS('PAPSRecord 필드명 마이그레이션을 시작합니다...'))
            self.stdout.write(self.style.WARNING('⚠️  데이터베이스 백업을 먼저 수행하시기 바랍니다.'))

        # 필드명 매핑 정의
        FIELD_MAPPINGS = {
            # SHUTTLE_RUN
            'shuttles_completed': 'shuttle_run',
            
            # LONG_RUN_WALK
            'total_time': 'long_run_walk',
            
            # STEP_TEST
            'palpation': 'is_palpation',
            'hr1': 'step_test_heart_rate_1',
            'hr2': 'step_test_heart_rate_2',
            'hr3': 'step_test_heart_rate_3',
            'pei': 'step_test_pei',
            
            # SIT_REACH
            'attempt1': 'sit_reach_first_attempt',
            'attempt2': 'sit_reach_second_attempt',
            'best_record': 'sit_reach_best_record',
            
            # COMPREHENSIVE_FLEXIBILITY
            'shoulder_left': 'flexibility_shoulder_left',
            'shoulder_right': 'flexibility_shoulder_right',
            'trunk_left': 'flexibility_body_left',
            'trunk_right': 'flexibility_body_right',
            'side_left': 'flexibility_side_left',
            'side_right': 'flexibility_side_right',
            'lower_left': 'flexibility_lower_body_left',
            'lower_right': 'flexibility_lower_body_right',
            'total_score': 'flexibility_total_score',
            
            # GRIP_STRENGTH
            'right_hand_1st': 'grip_strength_right_hand_1',
            'left_hand_1st': 'grip_strength_left_hand_1',
            'right_hand_2nd': 'grip_strength_right_hand_2',
            'left_hand_2nd': 'grip_strength_left_hand_2',
            'grip_strength': 'grip_strength_best',
            'best_grip': 'grip_strength_best',
            
            # FIFTY_METER_RUN
            'time': 'fifty_meter_run',
            
            # STANDING_LONG_JUMP
            'first_attempt': 'standing_long_jump_first_attempt',
            'second_attempt': 'standing_long_jump_second_attempt',
            
            # BMI
            'height': 'bmi_height',
            'weight': 'bmi_weight',
            'bmi': 'bmi_bmi',
            
            # CARDIO_PRECISION_TEST
            'avg_heart_rate': 'cardio_precision_avg_heart_rate',
            'cardio_precision_rest_hr1': 'cardio_precision_rest_heart_rate_1',
            'cardio_precision_rest_hr2': 'cardio_precision_rest_heart_rate_2',
            'cardio_precision_rest_hr3': 'cardio_precision_rest_heart_rate_3',
            'cardio_precision_rest_pei': 'cardio_precision_pei',
            'avg_intensity': 'cardio_precision_avg_intensity',
        }

        # PAPSActivity 정보 가져오기 (count 필드 특별 처리용)
        activities_map = {str(activity.id): activity.name for activity in PAPSActivity.objects.all()}

        # 처리 대상 레코드 조회
        queryset = PAPSRecord.objects.exclude(measurement_data={})
        
        if activity_filter:
            try:
                activity_obj = PAPSActivity.objects.get(name=activity_filter)
                queryset = queryset.filter(activity_id=activity_obj.id)
                self.stdout.write(f'특정 활동으로 필터링: {activity_filter}')
            except PAPSActivity.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'활동을 찾을 수 없습니다: {activity_filter}'))
                return

        total_records = queryset.count()
        self.stdout.write(f'처리 대상 레코드 수: {total_records}')

        if total_records == 0:
            self.stdout.write(self.style.WARNING('처리할 레코드가 없습니다.'))
            return

        processed_count = 0
        changed_count = 0

        with transaction.atomic():
            for record in queryset:
                original_data = record.measurement_data.copy()
                new_data = {}
                changes_made = False

                # 활동명 가져오기
                activity_name = activities_map.get(str(record.activity_id), 'UNKNOWN')

                for old_field, value in original_data.items():
                    new_field = old_field

                    # 특별 처리: count 필드
                    if old_field == 'count':
                        if activity_name == 'PUSH_UP':
                            new_field = 'push_up'
                        elif activity_name == 'SIT_UP':
                            new_field = 'sit_up'
                        else:
                            # 다른 활동에서는 count 필드 유지
                            new_field = 'count'
                    
                    # 일반 매핑 적용
                    elif old_field in FIELD_MAPPINGS:
                        new_field = FIELD_MAPPINGS[old_field]

                    # 특별 처리: SIT_REACH와 STANDING_LONG_JUMP의 best_record 구분
                    if old_field == 'best_record':
                        if activity_name == 'SIT_REACH':
                            new_field = 'sit_reach_best_record'
                        elif activity_name == 'STANDING_LONG_JUMP':
                            new_field = 'standing_long_jump_best_record'

                    new_data[new_field] = value

                    if new_field != old_field:
                        changes_made = True

                if changes_made:
                    if dry_run:
                        self.stdout.write(f'레코드 {record.id} ({activity_name}):')
                        self.stdout.write(f'  변경 전: {json.dumps(original_data, ensure_ascii=False, indent=2)}')
                        self.stdout.write(f'  변경 후: {json.dumps(new_data, ensure_ascii=False, indent=2)}')
                        self.stdout.write('---')
                    else:
                        record.measurement_data = new_data
                        record.save()
                        self.stdout.write(f'✓ 레코드 {record.id} ({activity_name}) 업데이트 완료')
                    
                    changed_count += 1

                processed_count += 1

                # 100개마다 진행상황 출력
                if processed_count % 100 == 0:
                    self.stdout.write(f'진행 상황: {processed_count}/{total_records}')

            if dry_run:
                # dry-run 모드에서는 트랜잭션 롤백
                transaction.set_rollback(True)

        # 최종 결과 출력
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'처리 완료!')
        self.stdout.write(f'전체 레코드: {total_records}')
        self.stdout.write(f'변경된 레코드: {changed_count}')
        self.stdout.write(f'변경 없는 레코드: {processed_count - changed_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드였으므로 실제 변경은 되지 않았습니다.'))
            self.stdout.write('실제 마이그레이션을 수행하려면 --dry-run 옵션 없이 실행하세요.')
        else:
            self.stdout.write(self.style.SUCCESS('마이그레이션이 성공적으로 완료되었습니다!'))