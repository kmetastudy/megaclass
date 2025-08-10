import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from physical_education.models import PAPSActivity


class Command(BaseCommand):
    help = 'PAPS Activity의 measurement_schema와 evaluation_criteria 업데이트'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 업데이트 없이 미리보기만 실행',
        )
        parser.add_argument(
            '--schema-only',
            action='store_true',
            help='measurement_schema만 업데이트',
        )
        parser.add_argument(
            '--criteria-only',
            action='store_true',
            help='evaluation_criteria만 업데이트',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        schema_only = options['schema_only']
        criteria_only = options['criteria_only']
        
        # 상호 배타적 옵션 검증
        if schema_only and criteria_only:
            self.stdout.write(
                self.style.ERROR('--schema-only와 --criteria-only는 동시에 사용할 수 없습니다.')
            )
            return
        
        # 업데이트 모드 표시
        if schema_only:
            update_mode = "measurement_schema만"
        elif criteria_only:
            update_mode = "evaluation_criteria만"
        else:
            update_mode = "measurement_schema와 evaluation_criteria 모두"
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드: 실제 업데이트는 하지 않습니다.'))
        
        self.stdout.write(self.style.SUCCESS(f'PAPS 스키마 업데이트를 시작합니다... ({update_mode})'))
        
        # JSON 파일 경로
        data_path = os.path.join(settings.BASE_DIR, 'physical_education', 'data')
        schemas_file = os.path.join(data_path, 'measurement_schemas.json')
        criteria_file = os.path.join(data_path, 'evaluation_criteria.json')
        
        # JSON 파일 로드 (필요한 것만)
        measurement_schemas = None
        evaluation_criteria = None
        
        try:
            if not criteria_only:
                with open(schemas_file, 'r', encoding='utf-8') as f:
                    measurement_schemas = json.load(f)
            
            if not schema_only:
                with open(criteria_file, 'r', encoding='utf-8') as f:
                    evaluation_criteria = json.load(f)
        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f'JSON 파일을 찾을 수 없습니다: {e}')
            )
            return
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'JSON 파일 파싱 오류: {e}')
            )
            return

        # 기존 PAPSActivity 조회
        activities = PAPSActivity.objects.all()
        
        if not activities.exists():
            self.stdout.write(
                self.style.ERROR('PAPSActivity 데이터가 없습니다. 먼저 PAPSActivity를 생성해주세요.')
            )
            return

        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f'총 {activities.count()}개의 활동을 확인합니다...')
        
        for activity in activities:
            activity_name = activity.name
            
            # 업데이트할 데이터 확인
            new_schema = None
            new_criteria = None
            skip_activity = False
            
            if not criteria_only:
                new_schema = measurement_schemas.get(activity_name)
                if new_schema is None:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {activity.get_name_display()}: measurement_schema를 찾을 수 없음')
                    )
                    if schema_only:  # schema_only 모드에서 스키마를 찾을 수 없으면 건너뛰기
                        skipped_count += 1
                        continue
                    skip_activity = True
            
            if not schema_only:
                new_criteria = evaluation_criteria.get(activity_name)
            
            try:
                if dry_run:
                    self.stdout.write(f'📋 {activity.get_name_display()}:')
                    if not criteria_only:
                        schema_status = "업데이트 예정" if new_schema else "변경 없음" if not skip_activity else "찾을 수 없음"
                        self.stdout.write(f'   - measurement_schema: {schema_status}')
                    if not schema_only:
                        criteria_status = "업데이트 예정" if new_criteria else "제거 예정 (선택평가)"
                        self.stdout.write(f'   - evaluation_criteria: {criteria_status}')
                else:
                    # 실제 업데이트 수행
                    old_schema = activity.measurement_schema
                    old_criteria = activity.evaluation_criteria
                    
                    # 선택적 업데이트
                    if not criteria_only and new_schema:
                        activity.measurement_schema = new_schema
                    if not schema_only:
                        activity.evaluation_criteria = new_criteria  # None일 수 있음 (선택평가)
                    
                    activity.save()
                    
                    # 변경사항 로깅
                    self.stdout.write(f'✅ {activity.get_name_display()}:')
                    
                    # measurement_schema 변경사항
                    if not criteria_only and new_schema and old_schema != new_schema:
                        old_fields = len(old_schema.get('fields', [])) if old_schema else 0
                        new_fields = len(new_schema.get('fields', []))
                        self.stdout.write(f'   - measurement_schema: {old_fields}개 → {new_fields}개 필드')
                    elif not criteria_only and not new_schema:
                        self.stdout.write(f'   - measurement_schema: 변경 없음')
                    
                    # evaluation_criteria 변경사항
                    if not schema_only and old_criteria != new_criteria:
                        if new_criteria is None:
                            self.stdout.write(f'   - evaluation_criteria: 제거됨 (선택평가)')
                        elif old_criteria is None:
                            self.stdout.write(f'   - evaluation_criteria: 새로 추가됨')
                        else:
                            self.stdout.write(f'   - evaluation_criteria: 업데이트됨')
                    elif not schema_only:
                        self.stdout.write(f'   - evaluation_criteria: 변경 없음')
                
                updated_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {activity.get_name_display()}: 업데이트 실패 - {str(e)}')
                )
                error_count += 1

        # 결과 요약
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== 업데이트 완료 ==='))
        
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
            
            if error_count == 0 and skipped_count == 0:
                self.stdout.write(self.style.SUCCESS('🎉 모든 PAPS 활동이 성공적으로 업데이트되었습니다!'))

        # 업데이트된 스키마 정보 표시
        if not dry_run and updated_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=== 업데이트 상세 정보 ==='))
            
            # measurement_schema 통계
            total_fields = sum(
                len(activity.measurement_schema.get('fields', []))
                for activity in PAPSActivity.objects.all()
                if activity.measurement_schema
            )
            
            # evaluation_criteria 통계
            activities_with_criteria = PAPSActivity.objects.exclude(
                evaluation_criteria__isnull=True
            ).count()
            
            self.stdout.write(f'📊 총 입력 필드 수: {total_fields}개')
            self.stdout.write(f'📊 평가 기준이 있는 활동: {activities_with_criteria}개')
            self.stdout.write(f'📊 선택평가 활동 (평가 기준 없음): {activities.count() - activities_with_criteria}개')