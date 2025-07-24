import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from physical_education.models import PAPSCategory, PAPSActivity


class Command(BaseCommand):
    help = 'PAPS 카테고리 및 활동 데이터 초기화'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('PAPS 데이터 초기화를 시작합니다...'))
        
        # JSON 파일 경로
        docs_path = os.path.join(settings.BASE_DIR, 'docs')
        schemas_file = os.path.join(docs_path, 'paps_measurement_schemas.json')
        criteria_file = os.path.join(docs_path, 'paps_evaluation_criteria.json')
        
        # JSON 파일 로드
        try:
            with open(schemas_file, 'r', encoding='utf-8') as f:
                measurement_schemas = json.load(f)
            
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

        # 기존 데이터 삭제 확인
        if PAPSCategory.objects.exists() or PAPSActivity.objects.exists():
            self.stdout.write(
                self.style.WARNING('기존 PAPS 데이터가 존재합니다. 삭제하고 다시 생성합니다.')
            )
            PAPSActivity.objects.all().delete()
            PAPSCategory.objects.all().delete()

        # PAPS 카테고리 생성
        categories_data = [
            # 필수평가 (5개)
            ('CARDIO', '심폐지구력', 'REQUIRED', 1),
            ('FLEXIBILITY', '유연성', 'REQUIRED', 2),
            ('STRENGTH', '근력/근지구력', 'REQUIRED', 3),
            ('AGILITY', '순발력', 'REQUIRED', 4),
            ('BODY_FAT', '비만', 'REQUIRED', 5),
            # 선택평가 (4개)
            ('CARDIO_PRECISION', '심폐지구력정밀평가', 'OPTIONAL', 6),
            ('BODY_FAT_RATE', '체지방률평가', 'OPTIONAL', 7),
            ('POSTURE', '자세평가', 'OPTIONAL', 8),
            ('SELF_BODY', '자기신체평가', 'OPTIONAL', 9),
        ]

        created_categories = {}
        for category_code, name, eval_type, order in categories_data:
            category = PAPSCategory.objects.create(
                name=category_code,
                evaluation_type=eval_type,
                order=order
            )
            created_categories[category_code] = category
            self.stdout.write(f'  카테고리 생성: {category.get_name_display()}')

        # PAPS 활동 생성
        activities_data = [
            # 필수평가 활동
            ('SHUTTLE_RUN', '왕복오래달리기', 'CARDIO'),
            ('LONG_RUN_WALK', '오래달리기 걷기', 'CARDIO'),
            ('STEP_TEST', '스텝검사', 'CARDIO'),
            ('SIT_REACH', '앉아윗몸앞으로굽히기', 'FLEXIBILITY'),
            ('COMPREHENSIVE_FLEXIBILITY', '종합유연성', 'FLEXIBILITY'),
            ('PUSH_UP', '팔굽혀펴기', 'STRENGTH'),
            ('SIT_UP', '윗몸 말아올리기', 'STRENGTH'),
            ('GRIP_STRENGTH', '악력', 'STRENGTH'),
            ('FIFTY_METER_RUN', '50m 달리기', 'AGILITY'),
            ('STANDING_LONG_JUMP', '제자리멀리뛰기', 'AGILITY'),
            ('BMI', '체질량 지수(BMI) 측정', 'BODY_FAT'),
            # 선택평가 활동
            ('CARDIO_PRECISION_TEST', '심폐지구력정밀평가', 'CARDIO_PRECISION'),
            ('BODY_FAT_RATE_TEST', '체지방률평가', 'BODY_FAT_RATE'),
            ('POSTURE_TEST', '자세평가', 'POSTURE'),
            ('SELF_BODY_TEST', '자기신체평가', 'SELF_BODY'),
        ]

        created_activities = 0
        for activity_code, name, category_code in activities_data:
            # 측정 스키마 가져오기
            measurement_schema = measurement_schemas.get(activity_code, {})
            
            # 평가 기준 가져오기
            activity_evaluation_criteria = evaluation_criteria.get(activity_code, {})
            if activity_evaluation_criteria:
                # calculation_field 추가 (평가에 사용할 필드)
                activity_evaluation_criteria['calculation_field'] = self._get_calculation_field(activity_code)
            
            # 활동 생성
            activity = PAPSActivity.objects.create(
                name=activity_code,
                category_id=created_categories[category_code].id,
                measurement_schema=measurement_schema,
                evaluation_criteria=activity_evaluation_criteria
            )
            created_activities += 1
            self.stdout.write(f'  활동 생성: {activity.get_name_display()}')

        self.stdout.write(
            self.style.SUCCESS(
                f'PAPS 데이터 초기화 완료! '
                f'카테고리: {len(created_categories)}개, '
                f'활동: {created_activities}개 생성'
            )
        )

    def _get_calculation_field(self, activity_code):
        """활동별 등급 계산에 사용할 필드명 반환"""
        calculation_fields = {
            'SHUTTLE_RUN': 'shuttles_completed',
            'LONG_RUN_WALK': 'total_seconds',
            'STEP_TEST': 'pei',
            'SIT_REACH': 'best_result',
            'COMPREHENSIVE_FLEXIBILITY': 'total_score',
            'PUSH_UP': 'repetitions',
            'SIT_UP': 'repetitions',
            'GRIP_STRENGTH': 'best_result',
            'FIFTY_METER_RUN': 'time_seconds',
            'STANDING_LONG_JUMP': 'best_result',
            'BMI': 'bmi',
            'CARDIO_PRECISION_TEST': 'avg_heart_rate',
            'BODY_FAT_RATE_TEST': 'body_fat_rate',
            'POSTURE_TEST': 'overall_evaluation',
            'SELF_BODY_TEST': 'question_1',  # 첫 번째 문항으로 임시 설정
        }
        return calculation_fields.get(activity_code, 'value')